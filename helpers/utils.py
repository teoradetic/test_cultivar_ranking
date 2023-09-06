def format_float(number):
    return f"{number:.2f}"


def camel_case_string(_str):
    """
    Transforms strings in standardized lower-snaked_cased format.
    Used mainly for standardizing column names in dataframes.
    """
    return _str.strip().replace(' ', '_').lower()


def title_case_string(_str):
    """
    Transforms strings in standardized Title Case format.
    Used mainly for standardizing column names in dataframes for human-readable presentations.
    """
    return _str.strip().replace('_', ' ').title()


def intersect_lists(lst1, lst2):
    return [x for x in lst1 if x in lst2]