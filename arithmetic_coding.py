import os
import struct

class ArithmeticCoder:
    def __init__(self, k):
        self.k = k
        self.R = 1 << k  # 2^k
        self.output = []
        
    def calculate_frequencies(self, data):
        # Создаем словарь частот байтов
        freq_dict = {}
        for byte in data:
            freq_dict[byte] = freq_dict.get(byte, 0) + 1
            
        # Создаем списки байтов и их частот
        symbols = sorted(freq_dict.keys())
        frequencies = [freq_dict[symbol] for symbol in symbols]
        
        return symbols, frequencies
    
    def write_bit(self, bit):
        self.output.append(bit)
        
    def bits_to_bytes(self, bits):
        # Преобразуем биты в байты
        bytes_data = bytearray()
        # Сначала записываем количество значащих бит в последнем байте
        padding_bits = (8 - len(bits) % 8) % 8
        bytes_data.append(padding_bits)
        
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            # Дополняем нулями если нужно
            while len(byte_bits) < 8:
                byte_bits.append(0)
            byte = 0
            for bit in byte_bits:
                byte = (byte << 1) | bit
            bytes_data.append(byte)
        return bytes_data
    
    def bytes_to_bits(self, bytes_data):
        # Преобразуем байты в биты
        padding_bits = bytes_data[0]  # Первый байт содержит количество padding-битов
        bits = []
        
        for byte in bytes_data[1:]:  # Пропускаем первый байт
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        
        # Удаляем padding-биты из последнего байта
        if padding_bits > 0 and len(bits) >= padding_bits:
            bits = bits[:-padding_bits]
        
        return bits
    
    def encode(self, data, symbols, frequencies, total_freq):
        # Преобразуем байты в индексы
        symbol_to_index = {symbol: i for i, symbol in enumerate(symbols)}
        indexed_data = [symbol_to_index[symbol] for symbol in data]
        
        l = 0
        u = self.R - 1
        m = 0
        
        for symbol_index in indexed_data:
            s = u - l + 1
            cum_freq = sum(frequencies[:symbol_index])
            
            u_new = l + (s * (cum_freq + frequencies[symbol_index]) // total_freq) - 1
            l_new = l + (s * cum_freq // total_freq)
            
            u = u_new
            l = l_new
            
            while True:
                if u < self.R // 2:
                    self.write_bit(0)
                    for _ in range(m):
                        self.write_bit(1)
                    m = 0
                    l = 2 * l
                    u = 2 * u + 1
                    
                elif l >= self.R // 2:
                    self.write_bit(1)
                    for _ in range(m):
                        self.write_bit(0)
                    m = 0
                    l = 2 * (l - self.R // 2)
                    u = 2 * (u - self.R // 2) + 1
                    
                elif l >= self.R // 4 and u < 3 * (self.R // 4):
                    m += 1
                    l = 2 * (l - self.R // 4)
                    u = 2 * (u - self.R // 4) + 1
                    
                else:
                    break
        
        if l >= self.R // 4:
            self.write_bit(1)
            for _ in range(m):
                self.write_bit(0)
            self.write_bit(0)
        else:
            self.write_bit(0)
            for _ in range(m):
                self.write_bit(1)
            self.write_bit(1)
            
        return self.output
    
    def read_bit(self, encoded_data, position):
        if position >= len(encoded_data):
            return 0
        return encoded_data[position]
    
    def decode(self, encoded_bits, symbols, frequencies, total_freq, n):
        # Предварительно вычисляем кумулятивные частоты
        cumulative_freqs = [0] * (len(frequencies) + 1)
        for i in range(len(frequencies)):
            cumulative_freqs[i + 1] = cumulative_freqs[i] + frequencies[i]
        
        def find_symbol(value):
            left, right = 0, len(frequencies) - 1
            while left <= right:
                mid = (left + right) // 2
                if cumulative_freqs[mid] <= value < cumulative_freqs[mid + 1]:
                    return mid
                elif value < cumulative_freqs[mid]:
                    right = mid - 1
                else:
                    left = mid + 1
            return left

        l = 0
        u = self.R - 1
        lb = 0
        ub = self.R - 1
        j = 0
        bit_pos = 0
        decoded_indices = []
        
        while j < n:
            s = u - l + 1
            
            # Вычисляем значение для поиска символа
            value = ((lb - l + 1) * total_freq - 1) // s
            
            # Используем бинарный поиск для нахождения символа
            symbol_index = find_symbol(value)
            
            u_new = l + (s * cumulative_freqs[symbol_index + 1] // total_freq) - 1
            l_new = l + (s * cumulative_freqs[symbol_index] // total_freq)
            
            if lb >= l_new and ub <= u_new:
                decoded_indices.append(symbol_index)
                u = u_new
                l = l_new
                j += 1
            else:
                bit = self.read_bit(encoded_bits, bit_pos)
                bit_pos += 1
                sb = ub - lb + 1
                lb = lb + bit * (sb // 2)
                ub = lb + (sb // 2) - 1
                continue
            
            while True:
                if l >= self.R // 2:
                    u = 2 * (u - self.R // 2) + 1
                    l = 2 * (l - self.R // 2)
                    ub = 2 * (ub - self.R // 2) + 1
                    lb = 2 * (lb - self.R // 2)
                    
                elif u < self.R // 2:
                    u = 2 * u + 1
                    l = 2 * l
                    ub = 2 * ub + 1
                    lb = 2 * lb
                    
                elif l >= self.R // 4 and u < 3 * (self.R // 4):
                    u = 2 * (u - self.R // 4) + 1
                    l = 2 * (l - self.R // 4)
                    ub = 2 * (ub - self.R // 4) + 1
                    lb = 2 * (lb - self.R // 4)
                    
                else:
                    break
        
        # Преобразуем индексы обратно в байты
        return bytes([symbols[i] for i in decoded_indices])

def compress_file(input_path):
    # Создаем имя для сжатого файла
    compressed_path = input_path + '.ac'
    
    # Читаем входной файл побайтово
    with open(input_path, 'rb') as f:
        input_data = f.read()
    
    # Создаем кодер
    #coder = ArithmeticCoder(k=16)
    coder = ArithmeticCoder(16)
    # Вычисляем частоты байтов
    symbols, frequencies = coder.calculate_frequencies(input_data)
    total_freq = sum(frequencies)
    
    # Кодируем данные
    encoded_bits = coder.encode(input_data, symbols, frequencies, total_freq)
    encoded_bytes = coder.bits_to_bytes(encoded_bits)
    
    # Сохраняем сжатые данные
    with open(compressed_path, 'wb') as f:
        # Записываем размер исходного файла
        f.write(struct.pack('<Q', len(input_data)))
        
        # Записываем количество символов
        f.write(struct.pack('<H', len(symbols)))
        
        # Записываем таблицу символов и частот
        for symbol, freq in zip(symbols, frequencies):
            # Используем 4 байта для частоты вместо 1 байта
            f.write(struct.pack('<BI', symbol, freq))
            
        # Записываем сжатые данные
        f.write(encoded_bytes)
    
    return compressed_path

def decompress_file(compressed_path):
    # Создаем имя для распакованного файла
    output_path = compressed_path[:-3] + '_decoded' + os.path.splitext(compressed_path[:-3])[1]
    
    # Читаем сжатый файл
    with open(compressed_path, 'rb') as f:
        # Читаем размер исходного файла
        original_size = struct.unpack('<Q', f.read(8))[0]
        
        # Читаем количество символов
        num_symbols = struct.unpack('<H', f.read(2))[0]
        
        # Читаем таблицу символов и частот
        symbols = []
        frequencies = []
        for _ in range(num_symbols):
            # Читаем 4 байта для частоты вместо 1 байта
            symbol, freq = struct.unpack('<BI', f.read(5))
            symbols.append(symbol)
            frequencies.append(freq)
        
        # Читаем сжатые данные
        encoded_bytes = f.read()
    
    # Создаем декодер
    decoder = ArithmeticCoder(k=16)
    
    # Преобразуем байты в биты
    encoded_bits = decoder.bytes_to_bits(encoded_bytes)
    
    # Декодируем данные
    total_freq = sum(frequencies)
    decoded_data = decoder.decode(encoded_bits, symbols, frequencies, total_freq, original_size)
    
    # Сохраняем распакованные данные
    with open(output_path, 'wb') as f:
        f.write(decoded_data)
    
    return output_path

def compare_files(file1_path, file2_path):
    # Сравниваем размеры файлов
    if os.path.getsize(file1_path) != os.path.getsize(file2_path):
        return False
    
    # Сравниваем содержимое файлов побайтово
    with open(file1_path, 'rb') as f1, open(file2_path, 'rb') as f2:
        # Читаем и сравниваем файлы блоками по 8192 байта
        while True:
            block1 = f1.read(8192)
            block2 = f2.read(8192)
            
            if block1 != block2:
                return False
            
            if not block1:  # Достигнут конец файла
                break
    
    return True

def main():
    # Получаем путь к файлу от пользователя
    input_path = input("Введите путь к файлу для сжатия: ")
    
    if not os.path.exists(input_path):
        print("Файл не найден!")
        return
    
    # Сжимаем файл
    print("\nСжимаем файл...")
    compressed_path = compress_file(input_path)
    
    # Выводим статистику сжатия
    original_size = os.path.getsize(input_path)
    compressed_size = os.path.getsize(compressed_path)
    compression_ratio = (original_size - compressed_size) / original_size * 100
    
    print(f"\nСтатистика сжатия:")
    print(f"Исходный размер: {original_size} байт")
    print(f"Сжатый размер: {compressed_size} байт")
    print(f"Степень сжатия: {compression_ratio:.2f}%")
    
    # Распаковываем файл
    print("\nРаспаковываем файл...")
    decompressed_path = decompress_file(compressed_path)
    
    # Проверяем целостность данных
    print("\nПроверяем целостность данных...")
    if compare_files(input_path, decompressed_path):
        print("Проверка успешна: файлы идентичны")
    else:
        print("ОШИБКА: файлы различаются!")
    
    print(f"\nГотово!")
    print(f"Сжатый файл сохранен как: {compressed_path}")
    print(f"Распакованный файл сохранен как: {decompressed_path}")

if __name__ == "__main__":
    main() 