from pygkit.signals import Signal, SignalBus, signal


class TestSignal:
    def test_connect_and_emit(self):
        sig = Signal("test")
        results = []
        sig.connect(lambda: results.append("called"))
        sig.emit()
        assert results == ["called"]

    def test_connect_multiple(self):
        sig = Signal("test")
        results = []
        sig.connect(lambda: results.append("a"))
        sig.connect(lambda: results.append("b"))
        sig.emit()
        assert results == ["a", "b"]

    def test_disconnect(self):
        sig = Signal("test")
        results = []
        cb = lambda: results.append("called")
        sig.connect(cb)
        sig.disconnect(cb)
        sig.emit()
        assert results == []

    def test_disconnect_all(self):
        sig = Signal("test")
        results = []
        sig.connect(lambda: results.append("a"))
        sig.connect(lambda: results.append("b"))
        sig.disconnect_all()
        sig.emit()
        assert results == []

    def test_duplicate_connect(self):
        sig = Signal("test")
        results = []
        cb = lambda: results.append("called")
        sig.connect(cb)
        sig.connect(cb)
        sig.emit()
        assert results == ["called"]

    def test_emit_args(self):
        sig = Signal("test")
        results = []
        sig.connect(lambda x, y: results.append((x, y)))
        sig.emit(1, 2)
        assert results == [(1, 2)]

    def test_emit_kwargs(self):
        sig = Signal("test")
        results = []
        sig.connect(lambda a=0, b=0: results.append((a, b)))
        sig.emit(a=3, b=4)
        assert results == [(3, 4)]

    def test_iadd(self):
        sig = Signal("test")
        results = []
        sig += lambda: results.append("called")
        sig.emit()
        assert results == ["called"]

    def test_isub(self):
        sig = Signal("test")
        results = []
        cb = lambda: results.append("called")
        sig += cb
        sig -= cb
        sig.emit()
        assert results == []

    def test_call_syntax(self):
        sig = Signal("test")
        results = []
        sig += lambda: results.append("called")
        sig()
        assert results == ["called"]

    def test_name(self):
        sig = Signal("my_signal")
        assert sig.name == "my_signal"

    def test_emit_error_does_not_break(self):
        sig = Signal("test")
        results = []
        sig.connect(lambda: (_ for _ in ()).throw(ValueError("bad")))
        sig.connect(lambda: results.append("ok"))
        sig.emit()
        assert results == ["ok"]

    def test_weak_ref_allows_gc(self):
        sig = Signal("test")
        results = []
        def cb():
            results.append("called")
        sig.connect(cb)
        sig.emit()
        assert results == ["called"]


class TestSignalBus:
    def test_create_signal(self):
        bus = SignalBus()
        sig = bus.create_signal("test")
        assert isinstance(sig, Signal)
        assert sig.name == "test"

    def test_create_signal_idempotent(self):
        bus = SignalBus()
        sig1 = bus.create_signal("test")
        sig2 = bus.create_signal("test")
        assert sig1 is sig2

    def test_get_signal(self):
        bus = SignalBus()
        bus.create_signal("test")
        sig = bus.get_signal("test")
        assert sig is not None
        assert sig.name == "test"

    def test_get_signal_missing(self):
        bus = SignalBus()
        assert bus.get_signal("nonexistent") is None

    def test_emit_via_bus(self):
        bus = SignalBus()
        bus.create_signal("test")
        results = []
        bus.connect("test", lambda: results.append("called"))
        bus.emit("test")
        assert results == ["called"]

    def test_emit_missing_signal(self):
        bus = SignalBus()
        bus.emit("nonexistent")

    def test_connect_missing_signal(self):
        bus = SignalBus()
        bus.connect("nonexistent", lambda: None)

    def test_disconnect_missing_signal(self):
        bus = SignalBus()
        bus.disconnect("nonexistent", lambda: None)

    def test_disconnect_via_bus(self):
        bus = SignalBus()
        bus.create_signal("test")
        results = []
        cb = lambda: results.append("called")
        bus.connect("test", cb)
        bus.disconnect("test", cb)
        bus.emit("test")
        assert results == []

    def test_bus_with_args(self):
        bus = SignalBus()
        bus.create_signal("test")
        results = []
        bus.connect("test", lambda x: results.append(x))
        bus.emit("test", 42)
        assert results == [42]


class TestSignalDescriptor:
    def test_descriptor_is_signal_on_instance(self):
        class Obj:
            sig = signal()

        obj = Obj()
        assert isinstance(obj.sig, Signal)

    def test_descriptor_unique_per_instance(self):
        class Obj:
            sig = signal()

        a = Obj()
        b = Obj()
        assert a.sig is not b.sig

    def test_descriptor_connect_and_emit(self):
        class Obj:
            sig = signal()

        obj = Obj()
        results = []
        obj.sig += lambda: results.append("called")
        obj.sig()
        assert results == ["called"]

    def test_descriptor_assign_allows_override(self):
        class Obj:
            sig = signal()

        obj = Obj()
        sig = obj.sig
        obj.sig = "nope"
        assert obj.sig == "nope"

    def test_descriptor_multiple_signals(self):
        class Obj:
            a = signal()
            b = signal()

        obj = Obj()
        results = []
        obj.a += lambda: results.append("a")
        obj.b += lambda: results.append("b")
        obj.a()
        assert results == ["a"]
        obj.b()
        assert results == ["a", "b"]

    def test_descriptor_class_access(self):
        class Obj:
            sig = signal()

        assert isinstance(Obj.sig, signal)
