from dataclasses import dataclass
from fractions import Fraction

F = Fraction

def f(value) -> Fraction:
    """Преобразует int, str или Fraction в точную дробь Fraction."""
    if isinstance(value, Fraction):
        return value
    return Fraction(value)


def variable_number(name: str) -> int:
    """Преобразует x17 в 17. Используется для однозначного выбора при равенстве вариантов."""
    return int(name[1:])


def show_number(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


@dataclass
class Tableau:
    # Каждая строка записывается в виде:
    # x_базисная + sum(a_ij * x_свободная_j) = b_i
    basis: list[str]
    free: list[str]
    A: list[list[Fraction]]
    b: list[Fraction]

    # Целевая функция хранится в виде:
    # W = q + sum(c_j * x_свободная_j)
    c: list[Fraction]
    q: Fraction

    def drop_free(self, variable: str) -> None:
        """Удаляет свободную искусственную переменную после выхода из базиса."""
        if variable not in self.free:
            return

        j = self.free.index(variable)
        self.free.pop(j)
        self.c.pop(j)

        for row in self.A:
            row.pop(j)


def print_table(T: Tableau, title: str) -> None:
    """Печатает сокращённую симплекс-таблицу."""
    headers = ["basis"] + T.free + ["b"]
    rows = []

    for i, basis_var in enumerate(T.basis):
        rows.append(
            [basis_var]
            + [show_number(x) for x in T.A[i]]
            + [show_number(T.b[i])]
        )

    # В конспекте в правом нижнем углу таблицы записывается -Q, а не Q.
    rows.append(
        ["c"]
        + [show_number(x) for x in T.c]
        + [show_number(-T.q)]
    )

    widths = [
        max(len(headers[j]), max(len(row[j]) for row in rows))
        for j in range(len(headers))
    ]

    def line(values):
        return " | ".join(
            str(values[j]).rjust(widths[j])
            for j in range(len(values))
        )

    print(f"\n{title}")
    print(line(headers))
    print("-+-".join("-" * w for w in widths))

    for i, row in enumerate(rows):
        if i == len(rows) - 1:
            print("-+-".join("-" * w for w in widths))
        print(line(row))

    print(f"Q = {show_number(T.q)},  -Q = {show_number(-T.q)}")


def canon(A, signs, b):
    """
    Приводит ограничения к каноническому виду.

    <=  -> добавляем переменную с коэффициентом +1
    >=  -> добавляем переменную с коэффициентом -1
    =   -> ничего не меняем

    Также делает все правые части b_i неотрицательными.
    """
    A = [[f(x) for x in row] for row in A]
    b = [f(x) for x in b]
    signs = list(signs)

    m = len(A)
    n = len(A[0])
    names = [f"x{i + 1}" for i in range(n)]

    # В канонической задаче правые части b_i должны быть неотрицательными.
    for i in range(m):
        if b[i] < 0:
            A[i] = [-x for x in A[i]]
            b[i] = -b[i]

            if signs[i] == "<=":
                signs[i] = ">="
            elif signs[i] == ">=":
                signs[i] = "<="

    for i, sign in enumerate(signs):
        if sign == "=":
            continue

        if sign not in ("<=", ">="):
            raise ValueError(f"Неизвестный знак ограничения: {sign}")

        names.append(f"x{len(names) + 1}")

        # Добавляем новый столбец для новой переменной.
        for row in A:
            row.append(F(0))

        A[i][-1] = F(1) if sign == "<=" else F(-1)

    return A, b, names


def start_aux(A, b, canonical_names):
    """
    Строит вспомогательную задачу так же, как в ручном решении:
    добавляет по одной искусственной переменной к каждому равенству.

    Wa = x_искусств1 + ... + x_искусств_m -> min.
    """
    m = len(A)
    first_artificial_number = len(canonical_names) + 1

    artificial = [
        f"x{first_artificial_number + i}"
        for i in range(m)
    ]

    # В начале все искусственные переменные являются базисными.
    basis = artificial.copy()
    free = canonical_names.copy()

    # x_искусств_i = b_i - sum_j(a_ij*x_j)
    # Wa = sum_i(b_i) - sum_j(sum_i(a_ij)*x_j)
    c = [
        -sum(A[i][j] for i in range(m))
        for j in range(len(free))
    ]
    q = sum(b, F(0))

    T = Tableau(
        basis=basis,
        free=free,
        A=[row.copy() for row in A],
        b=b.copy(),
        c=c,
        q=q,
    )

    return T, set(artificial)


def choose_entering(T: Tableau):
    """
    Выбирает переменную, которая входит в базис.

    Для задачи минимизации: если c_j < 0, увеличение соответствующей
    свободной переменной может уменьшить W.
    Выбираем самый отрицательный коэффициент.
    """
    candidates = [
        j for j, coefficient in enumerate(T.c)
        if coefficient < 0
    ]

    if not candidates:
        return None

    # Берём самый отрицательный коэффициент; при равенстве — переменную с меньшим номером.
    return min(
        candidates,
        key=lambda j: (T.c[j], variable_number(T.free[j])),
    )


def choose_leaving(
    T: Tableau,
    entering_col: int,
    artificial: set[str] | None = None,
):
    """
    Выбирает переменную, которая выходит из базиса.

    Используется тест отношений:
        min(b_i / a_ij), только для a_ij > 0.

    Во вспомогательной задаче при равенстве отношений стараемся
    вывести из базиса искусственную переменную.
    """
    candidates = []

    for i in range(len(T.basis)):
        a = T.A[i][entering_col]

        if a > 0:
            candidates.append((T.b[i] / a, i))

    if not candidates:
        raise RuntimeError(
            "В разрешающем столбце нет положительных элементов: "
            "целевая функция не ограничена в этом направлении."
        )

    min_ratio = min(ratio for ratio, _ in candidates)
    tied_rows = [
        i for ratio, i in candidates
        if ratio == min_ratio
    ]

    if artificial is not None:
        artificial_rows = [
            i for i in tied_rows
            if T.basis[i] in artificial
        ]

        if artificial_rows:
            tied_rows = artificial_rows

    return min(
        tied_rows,
        key=lambda i: variable_number(T.basis[i]),
    )


def pivot(T: Tableau, entering_col: int, leaving_row: int):
    """
    Выполняет один симплекс-переход.

    Входящая свободная переменная становится базисной,
    а выходящая базисная переменная становится свободной.

    Пересчёт выполняется тем же методом прямоугольника,
    который использовался в ручном решении.
    """
    old_A = [row.copy() for row in T.A]
    old_b = T.b.copy()
    old_c = T.c.copy()
    old_q = T.q
    old_basis = T.basis.copy()
    old_free = T.free.copy()

    p = old_A[leaving_row][entering_col]

    if p == 0:
        raise ZeroDivisionError("Разрешающий элемент не может быть равен нулю.")

    entering = old_free[entering_col]
    leaving = old_basis[leaving_row]

    # Меняем местами базисную и свободную переменные.
    T.basis[leaving_row] = entering
    T.free[entering_col] = leaving

    # 1. Пересчитываем разрешающую строку.
    for j in range(len(old_free)):
        if j == entering_col:
            # Этот столбец теперь соответствует переменной, вышедшей из базиса.
            T.A[leaving_row][j] = F(1) / p
        else:
            T.A[leaving_row][j] = (
                old_A[leaving_row][j] / p
            )

    T.b[leaving_row] = old_b[leaving_row] / p

    # 2. Пересчитываем остальные строки ограничений.
    for i in range(len(old_A)):
        if i == leaving_row:
            continue

        a_ie = old_A[i][entering_col]

        for j in range(len(old_free)):
            if j == entering_col:
                T.A[i][j] = -a_ie / p
            else:
                T.A[i][j] = (
                    old_A[i][j]
                    - a_ie * old_A[leaving_row][j] / p
                )

        T.b[i] = (
            old_b[i]
            - a_ie * old_b[leaving_row] / p
        )

    # 3. Пересчитываем нижнюю строку целевой функции.
    c_entering = old_c[entering_col]

    for j in range(len(old_free)):
        if j == entering_col:
            T.c[j] = -c_entering / p
        else:
            T.c[j] = (
                old_c[j]
                - c_entering * old_A[leaving_row][j] / p
            )

    T.q = (
        old_q
        + c_entering * old_b[leaving_row] / p
    )

    return entering, leaving, p


def phase(
    T: Tableau,
    name: str,
    artificial: set[str] | None = None,
    drop_artificial: bool = False,
):
    """Выполняет симплекс-шаги, пока все коэффициенты c_j не станут >= 0."""
    print_table(T, f"{name}:")

    step_number = 0

    while True:
        entering_col = choose_entering(T)

        if entering_col is None:
            break

        leaving_row = choose_leaving(
            T,
            entering_col,
            artificial,
        )

        entering_name = T.free[entering_col]
        leaving_name = T.basis[leaving_row]
        pivot_value = T.A[leaving_row][entering_col]

        step_number += 1

        print(
            f"Шаг {step_number}: "
            f"{entering_name} входит в базис, "
            f"{leaving_name} выходит; "
            f"pivot = {show_number(pivot_value)}"
        )

        _, leaving, _ = pivot(
            T,
            entering_col,
            leaving_row,
        )

        # В первой фазе искусственная переменная, вышедшая из базиса,
        # больше не нужна.
        if (
            drop_artificial
            and artificial is not None
            and leaving in artificial
        ):
            T.drop_free(leaving)

        print_table(
            T,
            f"{name}: после шага {step_number}",
        )


def to_main(
    T: Tableau,
    main_coefficients: dict[str, Fraction],
    artificial: set[str],
):
    """
    Переходит от вспомогательной задачи к основной.

    Удаляет искусственные переменные и заменяет Wa
    на настоящую целевую функцию W.

    Если:
        x_базис_i + sum_j(a_ij*x_j) = b_i,
    то:
        x_базис_i = b_i - sum_j(a_ij*x_j).

    Эти выражения подставляются в настоящую целевую функцию.
    """
    basic_artificial = [
        variable
        for variable in T.basis
        if variable in artificial
    ]

    if basic_artificial:
        raise RuntimeError(
            "В базисе остались искусственные переменные: "
            + ", ".join(basic_artificial)
        )

    for variable in list(T.free):
        if variable in artificial:
            T.drop_free(variable)

    q = F(0)
    c = [
        main_coefficients.get(variable, F(0))
        for variable in T.free
    ]

    for i, basis_variable in enumerate(T.basis):
        cb = main_coefficients.get(
            basis_variable,
            F(0),
        )

        q += cb * T.b[i]

        for j in range(len(T.free)):
            c[j] -= cb * T.A[i][j]

    T.q = q
    T.c = c


def read_solution(
    T: Tableau,
    original_variables: list[str],
):
    """
    Считывает базисное решение из таблицы.

    В базисной точке все свободные переменные равны 0,
    а базисные переменные равны соответствующим b_i.
    """
    values = {
        variable: F(0)
        for variable in T.basis + T.free
    }

    for i, variable in enumerate(T.basis):
        values[variable] = T.b[i]

    return {
        variable: values.get(variable, F(0))
        for variable in original_variables
    }


def check_original(
    x: dict[str, Fraction],
    objective_coefficients,
):
    x1 = x["x1"]
    x2 = x["x2"]
    x3 = x["x3"]
    x4 = x["x4"]

    lhs1 = x1 + x2 + 2 * x4
    lhs2 = x2 + x3 + x4
    lhs3 = 2 * x1 + x3

    Z = (
        objective_coefficients[0] * x1
        + objective_coefficients[1] * x2
        + objective_coefficients[2] * x3
        + objective_coefficients[3] * x4
    )

    print("\nПроверка в исходной задаче:")
    print(f"1) {show_number(lhs1)} <= 8")
    print(f"2) {show_number(lhs2)} = 6")
    print(f"3) {show_number(lhs3)} >= 2")
    print(f"Z = {show_number(Z)}")


def main():
    # Вариант 17
    # Z = x1 + 3*x2 + 2*x3 + x4 -> max
    objective = [F(1), F(3), F(2), F(1)]

    A = [
        [1, 1, 0, 2],
        [0, 1, 1, 1],
        [2, 0, 1, 0],
    ]

    signs = ["<=", "=", ">="]
    b = [8, 6, 2]

    # 1. Приводим задачу к каноническому виду.
    Aeq, beq, canonical_names = canon(
        A,
        signs,
        b,
    )

    # 2. Строим и решаем вспомогательную задачу.
    T, artificial = start_aux(
        Aeq,
        beq,
        canonical_names,
    )

    phase(
        T,
        name="ВСПОМОГАТЕЛЬНАЯ ЗАДАЧА",
        artificial=artificial,
        drop_artificial=True,
    )

    if T.q != 0:
        print(
            "\nWa != 0, поэтому область допустимых решений пуста."
        )
        return

    # 3. Возвращаем настоящую целевую функцию.
    # Решаем задачу на минимум, поэтому W = -Z.
    main_coefficients = {
        "x1": -objective[0],
        "x2": -objective[1],
        "x3": -objective[2],
        "x4": -objective[3],
    }

    # Добавочные переменные x5 и x6 в исходную целевую функцию не входят.
    for variable in canonical_names[4:]:
        main_coefficients[variable] = F(0)

    to_main(
        T,
        main_coefficients,
        artificial,
    )

    # 4. Решаем основную задачу симплекс-методом.
    phase(
        T,
        name="ОСНОВНАЯ ЗАДАЧА",
    )

    # 5. Считываем найденное базисное решение.
    x = read_solution(
        T,
        ["x1", "x2", "x3", "x4"],
    )

    Z = -T.q

    print("\nИТОГОВЫЙ ОТВЕТ")
    for variable in ["x1", "x2", "x3", "x4"]:
        print(
            f"{variable} = {show_number(x[variable])}"
        )

    print(f"Zmax = {show_number(Z)}")

    zero_reduced = [
        variable
        for variable, coefficient
        in zip(T.free, T.c)
        if coefficient == 0
    ]

    if zero_reduced:
        print(
            "Есть альтернативные оптимальные решения "
            "(нулевой коэффициент у свободной переменной: "
            + ", ".join(zero_reduced)
            + ")."
        )

    check_original(x, objective)


if __name__ == "__main__":
    main()