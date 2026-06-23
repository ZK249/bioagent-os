class BioAgentError(Exception):
    """根异常"""
    pass


class DataEngineError(BioAgentError):
    """数据引擎层异常"""
    pass


class LoaderError(DataEngineError):
    """加载器异常"""
    pass


class VectorDBError(BioAgentError):
    """向量库异常"""
    pass


class AgentError(BioAgentError):
    """Agent层异常"""
    pass


class MemoryError(AgentError):
    """记忆模块异常"""
    pass