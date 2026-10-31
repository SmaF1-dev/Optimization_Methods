from itertools import product
from math import inf


def solve_resource_dp(values, total_resource, allowed):
    """
    Решает задачу полного распределения целочисленного ресурса методом ДП.

    values[k][x]  — эффект этапа k при выделении x единиц ресурса.
    allowed[k]    — множество допустимых значений x на этапе k.
    total_resource — общий объём ресурса, который нужно распределить полностью.

    Возвращает:
        optimum — оптимальное значение;
        plans — все оптимальные планы;
        value — таблицу функций Беллмана;
        actions — все оптимальные управления для каждого состояния.
    """
    if not isinstance(total_resource, int) or total_resource < 0:
        raise ValueError("Объём ресурса должен быть неотрицательным целым числом.")
    if not values:
        raise ValueError("Необходимо задать хотя бы один этап.")
    if len(values) != len(allowed):
        raise ValueError("Для каждого этапа нужно задать множество допустимых управлений.")

    for k, (stage_values, stage_allowed) in enumerate(zip(values, allowed), start=1):
        if not stage_values:
            raise ValueError(f"Для этапа {k} не заданы значения эффекта.")
        for x in stage_allowed:
            if not isinstance(x, int) or x < 0:
                raise ValueError(f"Недопустимое управление {x} на этапе {k}.")
            if x not in stage_values:
                raise ValueError(
                    f"Для управления {x} на этапе {k} отсутствует значение эффекта."
                )

    n = len(values)

    value = [
        [-inf] * (total_resource + 1)
        for _ in range(n + 1)
    ]
    actions = [
        [[] for _ in range(total_resource + 1)]
        for _ in range(n)
    ]

    # После последнего этапа допустим только нулевой остаток.
    value[n][0] = 0

    # Обратный проход Беллмана.
    for k in range(n - 1, -1, -1):
        for state in range(total_resource + 1):
            for x in sorted(allowed[k]):
                if x > state:
                    continue

                future = value[k + 1][state - x]
                if future == -inf:
                    continue

                candidate = values[k][x] + future

                if candidate > value[k][state]:
                    value[k][state] = candidate
                    actions[k][state] = [x]
                elif candidate == value[k][state]:
                    actions[k][state].append(x)

    optimum = value[0][total_resource]
    if optimum == -inf:
        raise ValueError("Для заданных ограничений не существует допустимого плана.")

    # Прямой проход. Восстанавливаем все оптимальные планы.
    plans = []

    def restore(k, state, prefix):
        if k == n:
            if state == 0:
                plans.append(tuple(prefix))
            return

        for x in actions[k][state]:
            restore(k + 1, state - x, prefix + [x])

    restore(0, total_resource, [])

    return optimum, plans, value, actions


def brute_force(values, total_resource, allowed):
    best_value = -inf
    best_plans = []

    for plan in product(*(sorted(stage_allowed) for stage_allowed in allowed)):
        if sum(plan) != total_resource:
            continue

        result = sum(values[k][plan[k]] for k in range(len(values)))

        if result > best_value:
            best_value = result
            best_plans = [plan]
        elif result == best_value:
            best_plans.append(plan)

    return best_value, best_plans


def run_tests():
    # 1. Нулевой объём ресурса.
    optimum, plans, _, _ = solve_resource_dp([{0: 0}], 0, [{0}])
    assert optimum == 0
    assert plans == [(0,)]

    # 2. Один этап.
    optimum, plans, _, _ = solve_resource_dp(
        [{0: 0, 1: 3, 2: 7}],
        2,
        [{0, 1, 2}],
    )
    assert optimum == 7
    assert plans == [(2,)]

    # 3. Все эффекты равны нулю.
    zero_values = [
        {0: 0, 1: 0, 2: 0},
        {0: 0, 1: 0, 2: 0},
    ]
    optimum, plans, _, _ = solve_resource_dp(
        zero_values,
        2,
        [{0, 1, 2}, {0, 1, 2}],
    )
    assert optimum == 0
    assert set(plans) == {(0, 2), (1, 1), (2, 0)}

    # 4. Несколько оптимальных планов.
    tie_values = [
        {0: 0, 1: 1, 2: 2},
        {0: 0, 1: 1, 2: 2},
    ]
    optimum, plans, _, _ = solve_resource_dp(
        tie_values,
        2,
        [{0, 1, 2}, {0, 1, 2}],
    )
    assert optimum == 2
    assert set(plans) == {(0, 2), (1, 1), (2, 0)}

    # 5. Оптимально отдать весь ресурс одному этапу.
    optimum, plans, _, _ = solve_resource_dp(
        [
            {0: 0, 1: 1, 2: 4, 3: 10},
            {0: 0},
        ],
        3,
        [{0, 1, 2, 3}, {0}],
    )
    assert optimum == 10
    assert plans == [(3, 0)]

    # 6. Некорректный отрицательный ресурс.
    try:
        solve_resource_dp([{0: 0}], -1, [{0}])
    except ValueError:
        pass
    else:
        raise AssertionError("Ожидалась ошибка для отрицательного ресурса.")

    # 7. Для допустимого управления отсутствует значение эффекта.
    try:
        solve_resource_dp([{0: 0}], 1, [{0, 1}])
    except ValueError:
        pass
    else:
        raise AssertionError("Ожидалась ошибка для неполной таблицы значений.")


def print_variant_solution(values, total_resource, allowed, optimum, plans, value, actions):
    print("Практическая работа №4. Динамическое программирование")
    print("Вариант 17: Заказ на первую линию")
    print()

    print("Исходные ограничения:")
    print("x1 + x2 + x3 = 12")
    print("x1 >= 4, x2 >= 1, x3 >= 1")
    print()

    print("Третий этап:")
    for state in range(1, 8):
        print(
            f"S3 = {state}: V3 = {value[2][state]}, "
            f"оптимальное x3 = {actions[2][state]}"
        )
    print()

    print("Второй этап:")
    for state in range(2, 9):
        print(
            f"S2 = {state}: V2 = {value[1][state]}, "
            f"оптимальные x2 = {actions[1][state]}"
        )
    print()

    print("Первый этап, S1 = 12:")
    for x1 in sorted(allowed[0]):
        if x1 > total_resource:
            continue
        tail = value[1][total_resource - x1]
        if tail == -inf:
            continue
        candidate = values[0][x1] + tail
        print(
            f"x1 = {x1}: w1 = {values[0][x1]}, "
            f"S2 = {total_resource - x1}, V2 = {tail}, сумма = {candidate}"
        )
    print()

    print("Оптимальное значение:", optimum)
    print("Все оптимальные планы:")
    for plan in plans:
        stage_values = [values[k][plan[k]] for k in range(len(values))]
        print(
            f"  {plan}: {stage_values[0]} + {stage_values[1]} + "
            f"{stage_values[2]} = {sum(stage_values)}"
        )


def main():
    # Исходные данные варианта 17 отделены от алгоритма.
    values = [
        {1: 22, 2: 28, 3: 30, 4: 18, 5: 21, 6: 23, 7: 25, 8: 26, 9: 27, 10: 28, 11: 29},
        {1: 6, 2: 11, 3: 15, 4: 18, 5: 20, 6: 22, 7: 23, 8: 24, 9: 25, 10: 25, 11: 26},
        {1: 5, 2: 10, 3: 14, 4: 17, 5: 19, 6: 21, 7: 22, 8: 23, 9: 24, 10: 24, 11: 25},
    ]

    total_resource = 12

    # Первая линия запускается только при x1 >= 4.
    # Для второй и третьей линии требуется хотя бы одна смена.
    allowed = [
        set(range(4, 11)),
        set(range(1, 8)),
        set(range(1, 8)),
    ]

    optimum, plans, value, actions = solve_resource_dp(
        values,
        total_resource,
        allowed,
    )

    print_variant_solution(
        values,
        total_resource,
        allowed,
        optimum,
        plans,
        value,
        actions,
    )

    check_value, check_plans = brute_force(values, total_resource, allowed)

    assert optimum == check_value
    assert set(plans) == set(check_plans)

    print()
    print("Проверка полным перебором:", check_value)
    print("Планы перебора:", check_plans)

    run_tests()
    print("Дополнительные тесты: PASS")


if __name__ == "__main__":
    main()
