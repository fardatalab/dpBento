from .parser import Parser


class RDBParser(Parser):
    def __init__(self):
        super().__init__()
        self._add_rdb_arguments()

    def _add_rdb_arguments(self):
        self.parser.add_argument('--scale_factors', type=str, required=True, help='Scale factors for RDB benchmarks')
        self.parser.add_argument('--query', type=str, required=True, help='Query for RDB benchmarks')
        self.parser.add_argument('--execution_mode', type=str, required=True, help='Execution mode for RDB benchmarks')
        self.parser.add_argument('--threads', type=str, required=True, help='Thread numbers for RDB benchmarks')
        self.parser.add_argument("--scale_factors_description", help="Description of scale factors")
        self.parser.add_argument("--query_description", help="Description of the query")
        self.parser.add_argument("--execution_mode_description", help="Description of the execution mode")
        self.parser.add_argument("--threads_description", help="Description of the thread numbers")
        self.parser.add_argument("--metrics", nargs='+', help="Metrics to collect")

    def parse_arguments(self):
        return self.parser.parse_args()