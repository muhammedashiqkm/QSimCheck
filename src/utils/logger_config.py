import logging
import logging.handlers
import os
from datetime import datetime
from pythonjsonlogger import jsonlogger

os.makedirs('logs', exist_ok=True)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_record['ip_address'] = record.ip_address
        if hasattr(record, 'method'):
            log_record['method'] = record.method
        if hasattr(record, 'path'):
            log_record['path'] = record.path

class SensitiveDataFilter(logging.Filter):
    def __init__(self, patterns=None):
        super(SensitiveDataFilter, self).__init__()
        self.patterns = patterns or [
            'password', 'token', 'secret', 'key', 'auth', 
            'credential', 'jwt', 'api_key', 'apikey'
        ]
    
    def filter(self, record):
        if isinstance(record.msg, str):
            for pattern in self.patterns:
                if pattern in record.msg.lower():
                    record.msg = self._redact_sensitive_data(record.msg, pattern)
        return True
    
    def _redact_sensitive_data(self, message, pattern):
        if ":" in message:
            parts = message.split(":")
            for i, part in enumerate(parts):
                if pattern in part.lower() and i < len(parts) - 1:
                    parts[i+1] = " [REDACTED]"
            return ":".join(parts)
        return message

def setup_logging(app_name='flask-rag-app', log_level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    if logger.handlers:
        logger.handlers.clear()
    
    json_formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    app_log_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10485760,
        backupCount=10
    )
    app_log_handler.setFormatter(json_formatter)
    app_log_handler.setLevel(log_level)
    
    error_log_handler = logging.handlers.RotatingFileHandler(
        'logs/error.log', 
        maxBytes=10485760,
        backupCount=10
    )
    error_log_handler.setFormatter(json_formatter)
    error_log_handler.setLevel(logging.ERROR)
    
    access_log_handler = logging.handlers.TimedRotatingFileHandler(
        'logs/access.log',
        when='midnight',
        backupCount=30
    )
    access_log_handler.setFormatter(json_formatter)
    access_log_handler.setLevel(log_level)
    
    security_log_handler = logging.handlers.RotatingFileHandler(
        'logs/security.log',
        maxBytes=10485760,
        backupCount=10
    )
    security_log_handler.setFormatter(json_formatter)
    security_log_handler.setLevel(log_level)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    
    sensitive_filter = SensitiveDataFilter()
    app_log_handler.addFilter(sensitive_filter)
    error_log_handler.addFilter(sensitive_filter)
    access_log_handler.addFilter(sensitive_filter)
    security_log_handler.addFilter(sensitive_filter)
    console_handler.addFilter(sensitive_filter)
    
    logger.addHandler(app_log_handler)
    logger.addHandler(error_log_handler)
    logger.addHandler(console_handler)
    
    access_logger = logging.getLogger('access')
    access_logger.setLevel(log_level)
    access_logger.addHandler(access_log_handler)
    access_logger.propagate = False
    
    security_logger = logging.getLogger('security')
    security_logger.setLevel(log_level)
    security_logger.addHandler(security_log_handler)
    security_logger.propagate = False
    
    app_logger = logging.getLogger(app_name)
    app_logger.setLevel(log_level)
    
    return {
        'app_logger': app_logger,
        'access_logger': access_logger,
        'security_logger': security_logger
    }

def log_request(request, user_id=None):
    logger = logging.getLogger('access')
    
    request_id = os.urandom(8).hex()
    
    method = request.method
    path = request.path
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    extra = {
        'request_id': request_id,
        'ip_address': ip,
        'method': method,
        'path': path,
        'user_agent': user_agent
    }
    
    if user_id:
        extra['user_id'] = user_id
    
    logger.info(f"Request: {method} {path}", extra=extra)
    return request_id

def log_security_event(event_type, details, user_id=None, ip_address=None):
    logger = logging.getLogger('security')
    
    extra = {
        'event_type': event_type,
        'details': details
    }
    
    if user_id:
        extra['user_id'] = user_id
    
    if ip_address:
        extra['ip_address'] = ip_address
    
    logger.info(f"Security event: {event_type} - {details}", extra=extra)