import uuid

from typing import Union


def materialized_column_name(id: Union[str, uuid.UUID], external_id: str) -> str:
    """
    IF WE EVER CHANGE THIS, we have
    to make sure we migrate the existing tables
    or make a table to look this up
    :param id:
    :param external_id:
    :return:
    """
    raw = f'{str(id)}_{external_id}'
    return raw[:60] if len(raw) > 60 else raw


def materialized_table_name(id: Union[str, uuid.UUID], external_id: str) -> str:
    """
    IF WE EVER CHANGE THIS, we have
    to make sure we migrate the existing tables
    or make a table to look this up

    THIS IS ALSO USED IN MIGRATIONS!

    :param id:
    :param external_id:
    :return:
    """
    raw = f'_mat_{str(id)}_{external_id}'
    return raw[:60] if len(raw) > 60 else raw


def materialized_flat_history_table_name(id: Union[str, uuid.UUID], external_id: str) -> str:
    """
    IF WE EVER CHANGE THIS, we have
    to make sure we migrate the existing tables
    or make a table to look this up

    THIS IS ALSO USED IN MIGRATIONS!

    :param id:
    :param external_id:
    :return:
    """
    raw = f'_mfhist_{str(id)}_{external_id}'
    return raw[:60] if len(raw) > 60 else raw

