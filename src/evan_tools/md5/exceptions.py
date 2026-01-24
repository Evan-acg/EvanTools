"""
MD5 模块异常定义

这个模块定义了 MD5 计算过程中可能发生的所有异常。
"""


class HashCalculationError(Exception):
    """哈希计算异常基类

    所有与哈希计算相关的异常都应继承此类。
    """

    pass


class FileAccessError(HashCalculationError):
    """文件访问异常

    当文件不存在、无读取权限或其他访问问题时抛出。
    """

    pass


class FileReadError(HashCalculationError):
    """文件读取异常

    当读取文件内容时发生磁盘错误、I/O 中断等问题时抛出。
    """

    pass


class InvalidConfigError(HashCalculationError):
    """无效配置异常

    当配置参数无效或不合理时抛出。
    """

    pass
