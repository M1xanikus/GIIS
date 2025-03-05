
from typing import List
import tkinter as tk
from .algorithmsLine import LineStrategyInterface, LineContext, WuStrategy,DDAStrategy,BresenhamStrategy
from .algorithmsSecondOrderLine import SecondOrderLineContext, BresenhamCircleStrategy,BresenhamEllipseStrategy, BresenhamParabolaStrategy,BresenhamHyperbolaStrategy
from .baseLineContext import BaseLineContext


class BasicMenuClass:

    def __init__(self, root,line_btn, strategies: List[LineStrategyInterface], context: BaseLineContext, on_select ) :
        self.root = root
        self.strategies = strategies
        self.context = context
        self.line_btn = line_btn
        self.algorithm_menu = None  # Теперь создаётся только при вызове
        self.on_select = on_select  # Callback после выбора алгоритма

    def show_algorithm_menu(self):
        # Удаляем старое меню, если оно существует
        if self.algorithm_menu:
            self.algorithm_menu.destroy()

        # Создаём новое меню
        self.algorithm_menu = tk.Toplevel(self.root)
        x = self.line_btn.winfo_rootx() + self.line_btn.winfo_width()
        y = self.line_btn.winfo_rooty()

        self.algorithm_menu.geometry(f"150x{25 * len(self.strategies)}+{x}+{y}")
        self.algorithm_menu.overrideredirect(True)
        self.algorithm_menu.grab_set()

        for algorithm in self.strategies:
            btn = tk.Button(self.algorithm_menu, text=algorithm.name,
                            command=lambda alg=algorithm: self.select_algorithm(alg))
            btn.pack(fill=tk.X)

    def select_algorithm(self, alg):

        print(f"Выбран алгоритм: {alg.name}")

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
