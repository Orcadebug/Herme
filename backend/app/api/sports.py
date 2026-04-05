"""
Sports simulation API routes.
"""

from flask import jsonify, request

from . import sports_bp
from ..models.sports_workspace import SportsScenario, SportsWorkspaceManager
from ..models.task import TaskManager
from ..services.sports_planner import SportsPlannerService
from ..services.sports_reporter import SportsReportService
from ..services.sports_rule_packs import list_supported_sports
from ..services.sports_simulator import SportsSimulationService


planner_service = SportsPlannerService()
simulation_service = SportsSimulationService()
report_service = SportsReportService()
task_manager = TaskManager()


def _json_error(message: str, status_code: int):
    return jsonify({'success': False, 'error': message}), status_code


@sports_bp.route('/config', methods=['GET'])
def sports_config():
    return jsonify({
        'success': True,
        'data': {
            'supported_sports': list_supported_sports(),
        }
    })


@sports_bp.route('/game/plan', methods=['POST'])
def plan_game():
    data = request.get_json() or {}
    sport = data.get('sport', '').strip()
    home_team = data.get('home_team', '').strip()
    away_team = data.get('away_team', '').strip()
    if not sport or not home_team or not away_team:
        return _json_error('sport, home_team, and away_team are required', 400)

    try:
        workspace_id, task_id = planner_service.plan_match_async(
            sport=sport,
            league=data.get('league', '').strip(),
            home_team=home_team,
            away_team=away_team,
            game_context=data.get('game_context', '').strip(),
        )
        return jsonify({
            'success': True,
            'data': {
                'workspace_id': workspace_id,
                'task_id': task_id,
                'status': 'planning',
            }
        })
    except ValueError as exc:
        return _json_error(str(exc), 400)
    except RuntimeError as exc:
        return _json_error(str(exc), 503)


@sports_bp.route('/game/plan/status', methods=['GET'])
def plan_status():
    task_id = request.args.get('task_id')
    workspace_id = request.args.get('workspace_id')

    if task_id:
        task = task_manager.get_task(task_id)
        if not task:
            return jsonify({'success': False, 'error': f'Task {task_id} not found'}), 404
        return jsonify({'success': True, 'data': task.to_dict()})

    if workspace_id:
        workspace = SportsWorkspaceManager.get_workspace(workspace_id)
        if not workspace:
            return jsonify({'success': False, 'error': f'Workspace {workspace_id} not found'}), 404
        return jsonify({
            'success': True,
            'data': {
                'workspace_id': workspace_id,
                'status': workspace.status.value,
                'planning_task_id': workspace.planning_task_id,
                'error': workspace.error,
            }
        })

    return jsonify({'success': False, 'error': 'task_id or workspace_id is required'}), 400


@sports_bp.route('/game/<workspace_id>', methods=['GET'])
def get_workspace(workspace_id: str):
    workspace = SportsWorkspaceManager.get_workspace(workspace_id)
    if not workspace:
        return jsonify({'success': False, 'error': f'Workspace {workspace_id} not found'}), 404
    return jsonify({'success': True, 'data': workspace.to_dict()})


@sports_bp.route('/game/list', methods=['GET'])
def list_workspaces():
    limit = request.args.get('limit', 20, type=int)
    results = [workspace.to_dict() for workspace in SportsWorkspaceManager.list_workspaces(limit=limit)]
    return jsonify({'success': True, 'data': results, 'count': len(results)})


@sports_bp.route('/game/scenario', methods=['POST'])
def save_scenario():
    data = request.get_json() or {}
    workspace_id = data.get('workspace_id')
    if not workspace_id:
        return _json_error('workspace_id is required', 400)
    workspace = SportsWorkspaceManager.get_workspace(workspace_id)
    if not workspace:
        return _json_error(f'Workspace {workspace_id} not found', 404)

    try:
        workspace.scenario = SportsScenario.from_dict(data.get('scenario'))
        SportsWorkspaceManager.save_workspace(workspace)
        return jsonify({'success': True, 'data': workspace.to_dict()})
    except ValueError as exc:
        return _json_error(str(exc), 400)


@sports_bp.route('/game/simulate', methods=['POST'])
def simulate_game():
    data = request.get_json() or {}
    workspace_id = data.get('workspace_id')
    if not workspace_id:
        return _json_error('workspace_id is required', 400)
    try:
        simulation_id = simulation_service.start_simulation_async(workspace_id)
        state = simulation_service.get_state(workspace_id, simulation_id)
        return jsonify({'success': True, 'data': state.to_dict() if state else {'simulation_id': simulation_id}})
    except ValueError as exc:
        return _json_error(str(exc), 409)
    except RuntimeError as exc:
        return _json_error(str(exc), 503)


@sports_bp.route('/game/simulate/status', methods=['GET'])
def simulate_status():
    workspace_id = request.args.get('workspace_id')
    simulation_id = request.args.get('simulation_id')
    if not workspace_id:
        return jsonify({'success': False, 'error': 'workspace_id is required'}), 400
    state = simulation_service.get_state(workspace_id, simulation_id)
    if not state:
        return jsonify({'success': False, 'error': 'Simulation not found'}), 404
    return jsonify({'success': True, 'data': state.to_dict()})


@sports_bp.route('/game/events', methods=['GET'])
def get_events():
    workspace_id = request.args.get('workspace_id')
    simulation_id = request.args.get('simulation_id')
    if not workspace_id:
        return jsonify({'success': False, 'error': 'workspace_id is required'}), 400
    events = simulation_service.get_events(workspace_id, simulation_id)
    return jsonify({'success': True, 'data': events, 'count': len(events)})


@sports_bp.route('/game/report/generate', methods=['POST'])
def generate_report():
    data = request.get_json() or {}
    workspace_id = data.get('workspace_id')
    if not workspace_id:
        return _json_error('workspace_id is required', 400)
    try:
        result = report_service.generate_report_async(workspace_id)
        return jsonify({'success': True, 'data': result})
    except ValueError as exc:
        return _json_error(str(exc), 409)
    except RuntimeError as exc:
        return _json_error(str(exc), 503)


@sports_bp.route('/game/report/status', methods=['GET'])
def report_status():
    task_id = request.args.get('task_id')
    workspace_id = request.args.get('workspace_id')
    if task_id:
        task = task_manager.get_task(task_id)
        if not task:
            return jsonify({'success': False, 'error': f'Task {task_id} not found'}), 404
        return jsonify({'success': True, 'data': task.to_dict()})
    if workspace_id:
        workspace = SportsWorkspaceManager.get_workspace(workspace_id)
        if not workspace:
            return jsonify({'success': False, 'error': f'Workspace {workspace_id} not found'}), 404
        return jsonify({
            'success': True,
            'data': {
                'workspace_id': workspace_id,
                'report_id': workspace.latest_report_id,
                'task_id': workspace.latest_report_task_id,
            }
        })
    return jsonify({'success': False, 'error': 'task_id or workspace_id is required'}), 400


@sports_bp.route('/game/report', methods=['GET'])
def get_report():
    workspace_id = request.args.get('workspace_id')
    report_id = request.args.get('report_id')
    if not workspace_id:
        return jsonify({'success': False, 'error': 'workspace_id is required'}), 400
    report = report_service.get_report(workspace_id, report_id)
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'}), 404
    return jsonify({'success': True, 'data': report})


@sports_bp.route('/game/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    workspace_id = data.get('workspace_id')
    persona = data.get('persona', 'Match Analyst')
    message = data.get('message', '').strip()
    if not workspace_id or not message:
        return _json_error('workspace_id and message are required', 400)

    try:
        response = report_service.chat(
            workspace_id=workspace_id,
            persona_name=persona,
            message=message,
            chat_history=data.get('chat_history', []),
        )
        return jsonify({'success': True, 'data': response})
    except ValueError as exc:
        return _json_error(str(exc), 400)
    except RuntimeError as exc:
        return _json_error(str(exc), 503)
