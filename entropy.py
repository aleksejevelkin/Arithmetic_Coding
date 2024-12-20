import math
from collections import Counter
import os


def calculate_entropy(data):
    """
    Вычисляет энтропию по данным.
    :param data: массив байтов
    :return: энтропия в битах на символ
    """
    # Подсчитываем частоты каждого байта
    freq = Counter(data)
    total = len(data)

    # Рассчитываем энтропию
    entropy = -sum((count / total) * math.log2(count / total) for count in freq.values())
    return entropy


def calculate_compression_ratio(entropy, bits_per_symbol=8):
    return (entropy / bits_per_symbol) * 100


def main():
    # Запрашиваем путь к файлу у пользователя
    file_path = input("Введите путь к файлу для расчета энтропии: ").strip()

    # Проверяем, существует ли файл
    if not os.path.exists(file_path):
        print("Файл не найден!")
        return

    try:
        # Считываем содержимое файла по байтам
        with open(file_path, 'rb') as f:
            data = f.read()

        if not data:
            print("Файл пустой!")
            return

        # Вычисляем энтропию
        entropy = calculate_entropy(data)

        # Рассчитываем максимальную степень сжатия
        compression_ratio = calculate_compression_ratio(entropy)

        # Выводим результаты
        print(f"\nЭнтропия файла: {entropy:.4f} бит/символ")
        print(f"Максимальная степень сжатия: {compression_ratio:.2f}%")
        print(f"Исходный размер файла: {len(data)} байт")

    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")


if __name__ == "__main__":
    main()
