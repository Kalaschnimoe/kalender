class Error(Exception):
    pass

class NoStartzeit(Error):
    pass

class NoEndzeit(Error):
    pass

class NoDienstbezeichnung(Error):
    pass

class NoInternetConnection(Error):
    pass