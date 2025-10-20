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
2250705175430:453867
2250797696937:053207
2250797693376:558572
2250797691313:254813
2250797698014:254975
2250797692510:043837
93799386804:623745
93799385394:649150
2250708330833:95462810
2250708336140:698416
2250708337785:40353986
2250708331921:26135798
2250708331722:913372
2250708333182:379536
2250708337215:272471
2250708332643:459698
2250708339603:441517
2250708337082:319213
"""

    numbers = """
93799382186
93799384603
93799384608
93799389192
93799381369
93799386869
93799386326
93799386950
93799385893
93799385080
93799387920
93799388693
93799389263
93799380505
93799389969
93799382403
93799387595
93799386043
93799387958
93799388422
93799387447
93799383447
93799381637
93799386713
93799384170
93799381516
"""

    filter_obj = PhoneNumberFilter(successful, numbers)
    filter_obj.load_successful().load_numbers().filter()

    filter_obj.print_summary()
