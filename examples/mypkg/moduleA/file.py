from thatway import Setting


class FirstClass:
    my_attribute = Setting(True, desc="Whether 'my_attribute' is an attribute")

    max_instances = Setting(3, desc="Maximum number of instances")
