from aiogram.dispatcher.filters.state import State, StatesGroup

class UserState(StatesGroup):
    companionFound = State()
    choice = State()
    newCompanion = State()


class FSMData(StatesGroup):
    name = State()
    city = State()
    profile = State()
    company = State()
    role = State()
    usefulness = State()
