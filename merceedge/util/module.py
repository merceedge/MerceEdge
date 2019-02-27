import imp
import os
import inspect

def load_modules(path, base_class):
    modules = {}

    def _findModule(filename):
        _modules = {}
        sufix = os.path.splitext(filename)[1][1:]
        if sufix.lower() == "py":
            component = filename.split('.')
            t = imp.find_module(component[0], [path])

            module = imp.load_module(component[0], t[0], t[1], t[2])

            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    if issubclass(obj, base_class) and name != base_class.__name__:
                        # print obj.plugin_name
                        name = getattr(obj, "name", None)
                        if name is not None:
                            _modules[name] = obj
                        else:
                            name = obj.__name__
                            _modules[name] = obj
        return _modules

    for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                rtn = _findModule(filename)
                modules.update(rtn)
    return modules
    