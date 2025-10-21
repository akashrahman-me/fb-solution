"""
Phone Number Filter - Class-based implementation
Filters out successful phone numbers from a list of numbers to check
"""
from typing import List, Set


class PhoneNumberFilter:
    """Handles filtering of phone numbers based on successful results"""

    def __init__(self, successful_data: str = "", numbers_data: str = ""):
        """
        Initialize the filter with raw data

        Args:
            successful_data: Multi-line string with format "phone:code"
            numbers_data: Multi-line string with phone numbers
        """
        self.successful_data = successful_data
        self.numbers_data = numbers_data
        self._successful_numbers: Set[str] = set()
        self._all_numbers: List[str] = []
        self._filtered_numbers: List[str] = []

    def load_successful(self, data: str = None) -> 'PhoneNumberFilter':
        """
        Load successful phone numbers from data

        Args:
            data: Multi-line string with format "phone:code" (optional, uses init data if not provided)

        Returns:
            self for method chaining
        """
        data = data or self.successful_data
        self._successful_numbers = {
            line.split(":")[0].strip()
            for line in data.splitlines()
            if line.strip() and ":" in line
        }
        return self

    def load_numbers(self, data: str = None) -> 'PhoneNumberFilter':
        """
        Load all phone numbers to check

        Args:
            data: Multi-line string with phone numbers (optional, uses init data if not provided)

        Returns:
            self for method chaining
        """
        data = data or self.numbers_data
        self._all_numbers = [
            line.strip()
            for line in data.splitlines()
            if line.strip()
        ]
        return self

    def filter(self) -> 'PhoneNumberFilter':
        """
        Filter out successful numbers from all numbers

        Returns:
            self for method chaining
        """
        self._filtered_numbers = [
            num for num in self._all_numbers
            if num not in self._successful_numbers
        ]
        return self

    def print_summary(self):
        """Print a summary of the filtering"""
        print(f"Total numbers: {len(self._all_numbers)}")
        print(f"Successful numbers: {len(self._successful_numbers)}")
        print(f"Remaining to check: {len(self._filtered_numbers)}")
        print(f"\nFiltered numbers:")
        for num in self._filtered_numbers:
            print(num)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Sample data
    successful = """
2250715778343:36259467
2250715772775:789629
2250715770521:17042009
2250715779203:935528
"""

    numbers = """
2250715774457
2250715776049
2250715777573
2250715773443
2250715773725
2250715779203
2250715779821
2250715773140
2250715777761
2250715770618
2250715779038
2250715772866
2250715778684
2250715774608
2250715778171
2250715772758
2250715771858
2250715779267
2250715777338
2250715774450
2250715771945
2250715773345
2250715776450
2250715772022
2250715772378
2250715770521
2250715777429
2250715774921
2250715776943
2250715773983
2250715778643
2250715779619
2250715773959
2250715778952
2250715770236
2250715772775
2250715775410
2250715774263
2250715776536
2250715775787
2250715776233
2250715779156
2250715774888
2250715777180
2250715770026
2250715770266
2250715777970
2250715776042
2250715776175
2250715779608
2250715772206
2250715778048
2250715777090
2250715777733
2250715773737
2250715778343
2250715776566
2250715771466
2250715779233
2250715778030
2250715775240
2250715778962
2250715776835
2250715770546
2250715771302
2250715774878
2250715772568
2250715776014
2250715770393
2250715771863
2250715778539
2250715777700
2250715773193
2250715775874
2250715774882
2250715774341
2250715771975
2250715777196
2250715779588
2250715777909
2250715777259
2250715779813
2250715775464
2250715771412
2250715770859
2250715771824
2250715779686
2250715778074
2250715779989
2250715777835
2250715770605
2250715776589
2250715774123
2250715779730
2250715776431
2250715776679
2250715777047
2250715779318
2250715774674
2250715770601
"""

    filter_obj = PhoneNumberFilter(successful, numbers)
    filter_obj.load_successful().load_numbers().filter()

    filter_obj.print_summary()
