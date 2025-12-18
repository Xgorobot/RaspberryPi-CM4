import logging
def get_logger(name):

    logger = logging.getLogger(name)
    
    # 添加一些辅助方法
    def log_error_with_exc(msg, *args, **kwargs):
        """记录错误并自动包含异常堆栈"""
        kwargs['exc_info'] = True
        logger.error(msg, *args, **kwargs)
    
    # 添加到日志记录器
    logger.error_exc = log_error_with_exc
    
    return logger