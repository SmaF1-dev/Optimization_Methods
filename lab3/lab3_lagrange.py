import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

# Переменные задачи и множитель Лагранжа
x, y, lam = sp.symbols("x y lam", real=True)

# Вариант 5:
# f(x, y) = 2x - y -> extr
# x^2 + y^2 = 5
f = 2 * x - y
g = x**2 + y**2 - 5

# Функция Лагранжа: L = f + lambda * g
L = f + lam * g

# Условия первого порядка:
# dL/dx = 0, dL/dy = 0 и g = 0
equations = [
    sp.diff(L, x),
    sp.diff(L, y),
    g,
]

print("Функция Лагранжа:")
print("L =", L)

print("\nСистема Лагранжа:")
for eq in equations:
    print(sp.Eq(eq, 0))

# SymPy решает систему уравнений, а не задачу оптимизации целиком.
solutions = sp.solve(equations, (x, y, lam), dict=True)

print("\nНайденные кандидаты:")
results = []
for solution in solutions:
    point = {x: solution[x], y: solution[y]}

    # Проверка ограничения и значение целевой функции
    residual = sp.simplify(g.subs(point))
    value = sp.simplify(f.subs(point))

    # Проверка регулярности: grad g != 0
    grad_g = (
        sp.simplify(sp.diff(g, x).subs(point)),
        sp.simplify(sp.diff(g, y).subs(point)),
    )

    results.append((solution, residual, value, grad_g))

    print(
        f"x = {solution[x]}, y = {solution[y]}, lambda = {solution[lam]}, "
        f"g(x,y) = {residual}, f(x,y) = {value}, grad g = {grad_g}"
    )

# Определяем минимум и максимум среди найденных кандидатов.
min_result = min(results, key=lambda item: item[2])
max_result = max(results, key=lambda item: item[2])

print("\nИтог:")
print(
    "Глобальный минимум:",
    f"x = {min_result[0][x]}, y = {min_result[0][y]}, f = {min_result[2]}"
)
print(
    "Глобальный максимум:",
    f"x = {max_result[0][x]}, y = {max_result[0][y]}, f = {max_result[2]}"
)

# Визуализация
# Допустимое множество: окружность x^2 + y^2 = 5.
theta = np.linspace(0, 2 * np.pi, 600)
r = np.sqrt(5)
x_circle = r * np.cos(theta)
y_circle = r * np.sin(theta)

# Линии уровня целевой функции в экстремальных значениях:
# 2x - y = 5  -> y = 2x - 5
# 2x - y = -5 -> y = 2x + 5
x_line = np.linspace(-3.2, 3.2, 400)
f_max = float(max_result[2])
f_min = float(min_result[2])

# 2x - y = c  ->  y = 2x - c
y_max_level = 2 * x_line - f_max
y_min_level = 2 * x_line - f_min

plt.figure(figsize=(8, 7))
plt.plot(x_circle, y_circle, label=r"$x^2+y^2=5$")
plt.plot(x_line, y_max_level, label=r"$2x-y=5$")
plt.plot(x_line, y_min_level, label=r"$2x-y=-5$")
min_solution = min_result[0]
max_solution = max_result[0]

x_min = float(min_solution[x])
y_min = float(min_solution[y])

x_max = float(max_solution[x])
y_max = float(max_solution[y])

plt.scatter(
    [x_max, x_min],
    [y_max, y_min],
    s=80,
    zorder=5
)

plt.annotate(
    f"max ({x_max:g}, {y_max:g})",
    (x_max, y_max),
    xytext=(8, -18),
    textcoords="offset points"
)

plt.annotate(
    f"min ({x_min:g}, {y_min:g})",
    (x_min, y_min),
    xytext=(8, 10),
    textcoords="offset points"
)

plt.xlabel("x")
plt.ylabel("y")
plt.title("Метод множителей Лагранжа: вариант 5")
plt.grid(True)
plt.axis("equal")
plt.xlim(-3.2, 3.2)
plt.ylim(-3.2, 3.2)
plt.legend()
plt.tight_layout()
plt.savefig("lagrange_variant5_geometry.png", dpi=180)
plt.show()
