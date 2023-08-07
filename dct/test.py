from config import Config, Parameter

config = Config()

print(__name__)


# 1. class access
class Obj:

    a = Parameter("a", default=3)


print(f"Obj.a: {Obj.a}")
print(f"getattr(Obj, 'a'), {Obj.__getattribute__(Obj, 'a')}")
print(f"obj.a._caller_module_name: {Obj.__getattribute__(Obj, 'a')._caller_module_name}")

# 2. instance access
obj = Obj()
print(f"obj.a: {obj.a}")


# 3. direct access
# config.b = 2
# print(f"config.b: {config.b} (disallowed)")


# 4. direct parameter access
config.c = Parameter('c', default=3)

print(f"config.c: {config.c}")


print(f"config.__dict__: {config.__dict__}")
print(f"config.a: {config.a}")


# 5. Setting a new parameter should not be allowed
class NewObj:

    a = Parameter("a", default=5)

print(f"NewObj.a: {NewObj.a} (disallowed)")

