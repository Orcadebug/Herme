"""
Hermes Backend - Flask应用工厂
"""

import os
import warnings
from importlib import import_module

# 抑制 multiprocessing resource_tracker 的警告（来自第三方库如 transformers）
# 需要在所有其他导入之前设置
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask应用工厂函数"""
    errors = config_class.validate()
    if errors:
        raise RuntimeError("Invalid production configuration: " + "; ".join(errors))

    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 设置JSON编码：确保中文直接显示（而不是 \uXXXX 格式）
    # Flask >= 2.3 使用 app.json.ensure_ascii，旧版本使用 JSON_AS_ASCII 配置
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # 设置日志
    logger = setup_logger('hermes')
    
    # 只在 reloader 子进程中打印启动信息（避免 debug 模式下打印两次）
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info("Hermes Backend 启动中...")
        logger.info("=" * 50)
    
    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    disabled_components = []

    # 注册模拟进程清理函数（确保服务器关闭时终止所有模拟进程）
    try:
        from .services.simulation_runner import SimulationRunner
        SimulationRunner.register_cleanup()
        if should_log_startup:
            logger.info("已注册模拟进程清理函数")
    except ModuleNotFoundError as exc:
        disabled_components.append(f"simulation_cleanup:{exc.name}")
        logger.warning("跳过模拟进程清理注册，缺少依赖: %s", exc.name)
    
    # 请求日志中间件
    @app.before_request
    def log_request():
        logger = get_logger('hermes.request')
        logger.debug(f"请求: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"请求体: {request.get_json(silent=True)}")
    
    @app.after_request
    def log_response(response):
        logger = get_logger('hermes.request')
        logger.debug(f"响应: {response.status_code}")
        return response
    
    # 注册蓝图
    from .api import graph_bp, simulation_bp, report_bp, sports_bp

    import_module('.api.sports', __name__)
    app.register_blueprint(sports_bp, url_prefix='/api/sports')

    optional_blueprints = [
        ('.api.graph', graph_bp, '/api/graph', 'graph_api'),
        ('.api.simulation', simulation_bp, '/api/simulation', 'simulation_api'),
        ('.api.report', report_bp, '/api/report', 'report_api'),
    ]

    for module_name, blueprint, url_prefix, component_name in optional_blueprints:
        try:
            import_module(module_name, __name__)
            app.register_blueprint(blueprint, url_prefix=url_prefix)
        except ModuleNotFoundError as exc:
            disabled_components.append(f"{component_name}:{exc.name}")
            logger.warning("跳过注册 %s，缺少依赖: %s", component_name, exc.name)

    app.config['DISABLED_COMPONENTS'] = disabled_components
    
    # 健康检查
    @app.route('/health')
    def health():
        return {
            'status': 'ok',
            'service': 'Hermes Backend',
            'disabled_components': app.config.get('DISABLED_COMPONENTS', [])
        }
    
    if should_log_startup:
        logger.info("Hermes Backend 启动完成")
    
    return app
