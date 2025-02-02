from .parser import Parser


class KVSParser(Parser):
    def __init__(self):
        super().__init__()
        self._add_kvs_arguments()
        
    def _add_kvs_arguments(self):
        self.parser.add_argument('--operation_size', type=int, help='Operation sizes for KVS benchmarks')
        self.parser.add_argument('--operation_type', help='Operation types for KVS benchmarks')
        self.parser.add_argument('--data_distribution_type', type=str, help='Data distribution types for KVS benchmarks')
        self.parser.add_argument('--thread', type=int, help='Number of threads')
        self.parser.add_argument("--operation_size_description", help="Description of operation sizes")
        self.parser.add_argument("--operation_type_description", help="Description of operation types")
        self.parser.add_argument("--data_distribution_type_description", help="Description of data distribution types")
        self.parser.add_argument("--thread_description", help="Description of thread")
        self.parser.add_argument("--metrics", help="Metrics to collect, e.g., latency, runtime, throughput")

    def parse_arguments(self):
        return self.parser.parse_args()