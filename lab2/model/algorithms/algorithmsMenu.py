from typing import List
import tkinter as tk
from .algorithmsLine import LineStrategyInterface, LineContext, WuStrategy,DDAStrategy,BresenhamStrategy
from .algorithmsSecondOrderLine import SecondOrderLineContext, BresenhamCircleStrategy,BresenhamEllipseStrategy, BresenhamParabolaStrategy,BresenhamHyperbolaStrategy
from .baseLineContext import BaseLineContext
from model.algorithms.algorithmsCurves import HermiteCurve, BezierCurve, BSplineCurve, CurveContext, CurveStrategy


class BasicMenuClass:

    def __init__(self, root, line_btn, strategies: List, context: BaseLineContext, on_select):
        self.root = root
        self.strategies = strategies
        self.context = context
        self.line_btn = line_btn
        self.algorithm_menu = None
        self.on_select = on_select

    def show_algorithm_menu(self):
        if self.algorithm_menu:
            self.algorithm_menu.destroy()

        self.algorithm_menu = tk.Toplevel(self.root)
        x = self.line_btn.winfo_rootx() + self.line_btn.winfo_width()
        y = self.line_btn.winfo_rooty()

        num_strategies = len(self.strategies)
        menu_height = max(50, 25 * num_strategies)
        self.algorithm_menu.geometry(f"150x{menu_height}+{x}+{y}")
        self.algorithm_menu.overrideredirect(True)
        self.algorithm_menu.grab_set()

        for algorithm in self.strategies:
            algo_name = getattr(algorithm, 'name', type(algorithm).__name__)
            btn = tk.Button(self.algorithm_menu, text=algo_name,
                            command=lambda alg=algorithm: self.select_algorithm(alg))
            btn.pack(fill=tk.X)

    def select_algorithm(self, alg):
        algo_name = getattr(alg, 'name', type(alg).__name__)
        print(f"Выбран алгоритм: {algo_name}")
        self.context.set_strategy(alg)
        if self.algorithm_menu:
            self.algorithm_menu.destroy()
        if self.on_select:
            self.on_select()

class LineMenuClass(BasicMenuClass):
    def __init__(self, root,line_btn, context: LineContext,on_select):
        super().__init__(root, line_btn, [DDAStrategy(),WuStrategy(),BresenhamStrategy()], context,on_select)


class SecondOrderLineMenuClass(BasicMenuClass):
    def __init__(self, root, line_btn, context: SecondOrderLineContext, on_select):
        strategies = [
            BresenhamCircleStrategy(),
            BresenhamEllipseStrategy(),
            BresenhamHyperbolaStrategy(),
            BresenhamParabolaStrategy()
        ]
        super().__init__(root, line_btn, strategies, context, on_select)

class CurveMenuClass(BasicMenuClass):
    def __init__(self, root, button, context: CurveContext, on_select):
        strategies = [
            HermiteCurve(),
            BezierCurve(),
            BSplineCurve()
        ]
        strategies[0].name = "Кривая Эрмита"
        strategies[1].name = "Кривая Безье"
        strategies[2].name = "B-сплайн"

        super().__init__(root, button, strategies, context, on_select)
