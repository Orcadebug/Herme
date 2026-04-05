"""
Hermes Backend - Flask Application Factory
"""

import os
import warnings
from importlib import import_module

# Suppress multiprocessing resource_tracker warnings (from third-party libraries like transformers)
# Must be set before all other imports
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask application factory function"""
    errors = config_class.validate()
    if errors:
        raise RuntimeError("Invalid production configuration: " + "; ".join(errors))

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure JSON encoding: ensure Chinese characters display directly (not \uXXXX format)
    # Flask >= 2.3 uses app.json.ensure_ascii, older versions use JSON_AS_ASCII config
    if hasattr(app, "json") and hasattr(app.json, "ensure_ascii"):
        app.json.ensure_ascii = False

    # Set up logging
    logger = setup_logger("hermes")

    # Only print startup info in the reloader subprocess (avoid printing twice in debug mode)
    is_reloader_process = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    debug_mode = app.config.get("DEBUG", False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("Hermes Backend starting...")
        logger.info("=" * 50)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    disabled_components = []

    # Register simulation process cleanup function (ensure all simulation processes are terminated on server shutdown)
    try:
        from .services.simulation_runner import SimulationRunner

        SimulationRunner.register_cleanup()
        if should_log_startup:
            logger.info("Simulation process cleanup function registered")
    except ModuleNotFoundError as exc:
        disabled_components.append(f"simulation_cleanup:{exc.name}")
        logger.warning("跳过模拟进程清理注册，缺少依赖: %s", exc.name)

    # Request logging middleware
    @app.before_request
    def log_request():
        logger = get_logger("hermes.request")
        logger.debug(f"Request: {request.method} {request.path}")
        if request.content_type and "json" in request.content_type:
            logger.debug(f"Request body: {request.get_json(silent=True)}")

    @app.after_request
    def log_response(response):
        logger = get_logger("hermes.request")
        logger.debug(f"Response: {response.status_code}")
        return response

    # Register blueprints
    from .api import sports_bp

    import_module(".api.sports", __name__)
    app.register_blueprint(sports_bp, url_prefix="/api/sports")

    app.config["DISABLED_COMPONENTS"] = disabled_components

    # 健康检查
    @app.route("/health")
    def health():
        return {
            "status": "ok",
            "service": "Hermes Backend",
            "disabled_components": app.config.get("DISABLED_COMPONENTS", []),
        }

    if should_log_startup:
        logger.info("Hermes Backend 启动完成")

    return app
