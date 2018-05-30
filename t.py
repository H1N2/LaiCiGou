# coding = utf-8
print('This is a \033[1;93m test \033[0m!')
print('This is a \033[1;32;43m test \033[0m!')
print('\033[1;33;44mThis is a test !\033[0m')


class ConsoleColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

print(ConsoleColors.WARNING + "Warning: No active frommets remain. Continue?"+ ConsoleColors.ENDC)