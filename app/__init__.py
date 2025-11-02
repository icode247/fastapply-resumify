# app/__init__.py
"""
Application initialization module with Redis caching and enhanced logging.
"""
from flask import Flask, jsonify
from flask_cors import CORS
import logging

def create_app(config_object=None):
    """
    Create and configure the Flask application
    """
    from app.utils.logging import create_app_logger, RequestLogger
    from app.utils.redis_cache import cache_response, redis_client, get_cache_stats
    
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = '/tmp'

    # Load configuration if provided
    if config_object:
        app.config.from_object(config_object)

    # Setup CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
    
    # Setup enhanced logging
    logger = create_app_logger('resumify-api')
    RequestLogger(app, logger)
    
    # Check Redis connection
    try:
        redis_client.ping()
        logger.info("Successfully connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}", exc_info=True)

    # Import and register blueprints
    from app.api.match import bp as match_bp
    from app.api.parse import bp as parse_bp
    from app.api.optimize import bp as optimize_bp
    from app.api.generate import bp as generate_bp
    from app.api.resignation import bp as resignation_bp
    from app.api.jobdesc import bp as job_description_bp
    from app.api.linkedin import bp as linkedin_features_bp
    from app.api.coverletter import bp as coverletter_bp
    from app.api.resume_score import bp as resume_score_bp
    from app.api.resume_tracker import bp as resume_tracker_bp
    from app.api.upload import bp as upload_bp
    from app.api.linkedin_headline import bp as linkedin_headline_bp
    from app.api.linkedin_hashtags import bp as linkedin_hashtags_bp
    from app.api.interview import bp as interview_bp
    from app.api.intelligent_parse import bp as intelligent_parse_bp
    from app.api.job_match_ai import bp as job_match_ai_bp


    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(match_bp, url_prefix='/api')
    app.register_blueprint(parse_bp, url_prefix='/api')
    app.register_blueprint(optimize_bp, url_prefix='/api')
    app.register_blueprint(generate_bp, url_prefix='/api')
    app.register_blueprint(resignation_bp, url_prefix='/api')
    app.register_blueprint(job_description_bp, url_prefix='/api')
    app.register_blueprint(linkedin_features_bp, url_prefix='/api')
    app.register_blueprint(coverletter_bp, url_prefix='/api')
    app.register_blueprint(resume_score_bp, url_prefix='/api')
    app.register_blueprint(resume_tracker_bp, url_prefix='/api')
    app.register_blueprint(linkedin_headline_bp, url_prefix='/api')
    app.register_blueprint(linkedin_hashtags_bp, url_prefix='/api')
    app.register_blueprint(interview_bp, url_prefix='/api')  
    app.register_blueprint(intelligent_parse_bp, url_prefix='/api')
    app.register_blueprint(job_match_ai_bp, url_prefix='/api')

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    @cache_response(expiration=60)  # Cache for 1 minute
    def health_check():
        redis_status = "connected" if redis_client.ping() else "disconnected"
        cache_stats = get_cache_stats()
        
        return jsonify({
            "status": "healthy",
            "redis": redis_status,
            "cache": cache_stats
        })


    @app.route('/debug/memory-profile', methods=['GET'])
    def memory_profile():
        import tracemalloc
        import gc
        
        # Collect garbage before profiling
        gc.collect()
        
        # Start memory tracking
        tracemalloc.start()
        
        # Get current snapshot
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        # Format results
        memory_usage = []
        for stat in top_stats[:20]:  # Top 20 memory users
            memory_usage.append({
                'file': str(stat.traceback.frame.filename),
                'line': stat.traceback.frame.lineno,
                'size_kb': stat.size / 1024
            })
        
        # Stop tracking to clean up
        tracemalloc.stop()
        
        return jsonify({
            'memory_usage': memory_usage,
            'total_allocated': tracemalloc.get_traced_memory()[0] / (1024 * 1024)  # MB
        })

    # Error handlers
    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File too large"}), 413

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"error": "Rate limit exceeded"}), 429

    return app

