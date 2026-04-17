"""
Orchestrator Node

planned_steps'i sırayla işler:
  - Bağımlılık kontrolü yapar
  - Hatalı adım varsa bağımlıları atlar
  - Her supervisor'ı çalıştırır
  - Sonuçları execution_log ve supervisor_results'a yazar
  - MainState'teki context alanlarını günceller (user_id, team_id, vb.)
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.chat_service.state.main_state import MainState, ExecutionLogEntry, SupervisorResult
from src.services.chat_service.state.subgraph_state import SubgraphResult
from src.services.chat_service.supervisors.users_supervisor import run_users_supervisor
from src.services.chat_service.supervisors.teams_supervisor import run_teams_supervisor

logger = logging.getLogger(__name__)


def _dependencies_met(
    supervisor: str,
    dependencies: dict[str, list[str]],
    supervisor_results: dict[str, SupervisorResult],
    failed_steps: set[str],
) -> tuple[bool, str]:
    """
    Supervisor'ın bağımlılıkları karşılanmış mı kontrol eder.
    Returns: (karşılandı_mı, neden_atlandı)
    """
    deps = dependencies.get(supervisor, [])
    for dep in deps:
        if dep in failed_steps:
            return False, f"Bağımlı adım başarısız: {dep}"
        if dep not in supervisor_results:
            return False, f"Bağımlı adım henüz çalışmadı: {dep}"
    return True, ""


def _extract_context_updates(
    supervisor: str,
    result: SubgraphResult,
) -> dict:
    """
    Supervisor sonucundan MainState context alanlarını günceller.
    user_id, team_id, coins, level gibi değerleri çıkarır.
    """
    updates = {}
    if not result["success"] or not result["output"]:
        return updates

    output = result["output"]

    if supervisor == "users_supervisor":
        if "user_id" in output:
            updates["current_user_id"] = output["user_id"]
        if "coins" in output:
            updates["user_coins"] = output["coins"]
        if "new_level" in output:
            updates["user_level"] = output["new_level"]
        elif "level" in output:
            updates["user_level"] = output["level"]

    elif supervisor == "teams_supervisor":
        if "team_id" in output and output["team_id"] is not None:
            updates["current_team_id"] = output["team_id"]

    return updates


async def orchestrator_node(state: MainState, session: AsyncSession) -> dict:
    """
    Tüm planned_steps'i sırayla çalıştıran ana orchestration node.
    """
    planned_steps: list[str] = state.get("planned_steps", [])
    dependencies: dict = state.get("dependencies", {})
    instructions: dict = state.get("instructions", {})

    supervisor_results: dict[str, SupervisorResult] = {}
    execution_log: list[ExecutionLogEntry] = []
    completed_steps: list[str] = []
    failed_steps: set[str] = set()

    # Mevcut context
    current_user_id = state.get("current_user_id")
    current_user_role = state.get("current_user_role")
    current_team_id = state.get("current_team_id")
    user_coins = state.get("user_coins")
    user_level = state.get("user_level")

    if not planned_steps:
        return {
            "execution_log": [{
                "supervisor": "orchestrator",
                "success": False,
                "summary": "Hiçbir adım planlanmadı.",
                "output": None,
            }],
            "supervisor_results": {},
            "completed_steps": [],
        }

    for supervisor in planned_steps:
        # Bağımlılık kontrolü
        can_run, skip_reason = _dependencies_met(
            supervisor, dependencies, supervisor_results, failed_steps
        )

        if not can_run:
            logger.warning(f"[orchestrator] {supervisor} atlanıyor: {skip_reason}")
            failed_steps.add(supervisor)
            execution_log.append({
                "supervisor": supervisor,
                "success": False,
                "summary": f"Atlandı — {skip_reason}",
                "output": None,
            })
            continue

        # Talimatı al
        instruction = instructions.get(supervisor, "Gerekli işlemi yap.")

        logger.info(f"[orchestrator] {supervisor} başlatılıyor...")

        try:
            # Supervisor'ı çalıştır
            if supervisor == "users_supervisor":
                result: SubgraphResult = await run_users_supervisor(
                    instruction=instruction,
                    current_user_id=current_user_id,
                    current_user_role=current_user_role,
                    session=session,
                )

            elif supervisor == "teams_supervisor":
                result: SubgraphResult = await run_teams_supervisor(
                    instruction=instruction,
                    current_user_id=current_user_id,
                    current_user_role=current_user_role,
                    current_team_id=current_team_id,
                    session=session,
                )

            else:
                logger.error(f"[orchestrator] Bilinmeyen supervisor: {supervisor}")
                result: SubgraphResult = {
                    "success": False,
                    "output": None,
                    "error": f"Bilinmeyen supervisor: {supervisor}",
                    "retried": 0,
                }

        except Exception as e:
            logger.exception(f"[orchestrator] {supervisor} exception!")
            result: SubgraphResult = {
                "success": False,
                "output": None,
                "error": f"Beklenmeyen hata: {str(e)}",
                "retried": 0,
            }

        # Sonucu kaydet
        supervisor_results[supervisor] = result

        if result["success"]:
            completed_steps.append(supervisor)

            # Context'i güncelle (user_id, team_id, vb.)
            ctx_updates = _extract_context_updates(supervisor, result)
            if "current_user_id" in ctx_updates:
                current_user_id = ctx_updates["current_user_id"]
            if "current_team_id" in ctx_updates:
                current_team_id = ctx_updates["current_team_id"]
            if "user_coins" in ctx_updates:
                user_coins = ctx_updates["user_coins"]
            if "user_level" in ctx_updates:
                user_level = ctx_updates["user_level"]

            summary = f"Başarılı. Çıktı: {result['output']}"
            logger.info(f"[orchestrator] {supervisor} ✓")
        else:
            failed_steps.add(supervisor)
            summary = f"Başarısız. Hata: {result['error']} (deneme: {result['retried']})"
            logger.warning(f"[orchestrator] {supervisor} ✗ — {result['error']}")

        execution_log.append({
            "supervisor": supervisor,
            "success": result["success"],
            "summary": summary,
            "output": result.get("output"),
        })

    return {
        "supervisor_results": supervisor_results,
        "execution_log": execution_log,
        "completed_steps": completed_steps,
        "current_step": None,
        # Context güncellemeleri
        "current_user_id": current_user_id,
        "current_team_id": current_team_id,
        "user_coins": user_coins,
        "user_level": user_level,
    }
