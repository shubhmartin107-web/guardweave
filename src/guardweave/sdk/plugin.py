from __future__ import annotations

import importlib
import logging

from guardweave.core.models import ActionContext, PolicyEvaluationResult

logger = logging.getLogger("guardweave.sdk.plugin")


class GuardWeavePlugin:
    name: str = ""
    version: str = "1.0"

    async def before_evaluate(self, context: ActionContext) -> ActionContext:
        return context

    async def after_evaluate(
        self, context: ActionContext, result: PolicyEvaluationResult
    ) -> PolicyEvaluationResult:
        return result

    async def on_startup(self) -> None:
        pass

    async def on_shutdown(self) -> None:
        pass


class PluginManager:
    def __init__(self) -> None:
        self._plugins: dict[str, GuardWeavePlugin] = {}

    def register(self, plugin: GuardWeavePlugin) -> None:
        name = plugin.name or plugin.__class__.__name__
        self._plugins[name] = plugin
        logger.info("Registered plugin: %s v%s", name, plugin.version)

    def load_from_module(self, module_path: str, class_name: str) -> GuardWeavePlugin:
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            plugin: GuardWeavePlugin = cls()
            self.register(plugin)
            return plugin
        except (ImportError, AttributeError) as e:
            logger.error("Failed to load plugin %s.%s: %s", module_path, class_name, e)
            raise

    def get(self, name: str) -> GuardWeavePlugin | None:
        return self._plugins.get(name)

    def list(self) -> list[str]:
        return list(self._plugins.keys())

    async def run_before_evaluate(self, context: ActionContext) -> ActionContext:
        for plugin in self._plugins.values():
            context = await plugin.before_evaluate(context)
        return context

    async def run_after_evaluate(
        self, context: ActionContext, result: PolicyEvaluationResult
    ) -> PolicyEvaluationResult:
        for plugin in self._plugins.values():
            result = await plugin.after_evaluate(context, result)
        return result
