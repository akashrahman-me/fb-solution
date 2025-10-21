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
2250702294903:65101857
2250702295944:730628
2250702295451:082171
2250702295940:563318
2250702292215:815756
2290193595932:117255
261386706889:431418
261386701714:169014
261386708307:921598
261386700412:92267764
261386704907:377542
261386707005:95948385
996500670708:66835484
261386705545:419092
996500676869:558817
996500677736:420733
996500674110:764623
"""

    numbers = """2290193595932
59175875389
59175876275
59175873866
59175870652
59175870867
59175871798
59175879271
59175874759
59175873049
59175879747
59175875296
59175875349
59175870241
59175871000
59175878147
59175879232
59175876720
59175875003
59175870751
59175874405
59175870455
59175871438
59175879229
59175873451
59175876722
59175878820
59175872689
59175877763
59175878403
59175871624
59175878969
59175872821
59175876642
59175879253
59175879239
59175875944
59175875322
59175875387
59175875197
2250704236474
2250704233070
2250704239657
2250704233368
2250704231860
2250704238622
2250704232239
2250704235265
2250704236643
2250704234442
2250704235564
2250704235469
2250704235544
2250704233675
2250704236585
2250704238575
2250704230768
996500677104
996500674110
996500670976
996500673505
996500672800
996500674105
996500676869
996500677998
996500676922
996500673633
996500677736
996500673557
996500672937
996500674968
996500679443
996500677701
996500679802
996500677710
996500677122
996500674923
996500671581
996500676723
996500676517
996500671180
996500672489
996500673693
996500670708
261386705545
261386706971
261386704907
261386707005
261386707247
261386704324
261386700412
261386709021
261386704796
261386705876
261386700625
261386708307
261386701714
261386700632
261386706889
261386706738
261386709172
261386707465
261386707723
261386701525
261386707300
261386704241"""

    filter_obj = PhoneNumberFilter(successful, numbers)
    filter_obj.load_successful().load_numbers().filter()

    filter_obj.print_summary()
