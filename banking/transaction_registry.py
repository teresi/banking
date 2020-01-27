
REGISTERED_TRANSACTION_PARSERS = []

def register_parser(cls):
	REGISTERED_TRANSACTION_PARSERS.append(cls)
	return cls
