import sys
from gto.qualification import sparse_solver as s,sparse_study as st
mode=sys.argv[1];seed=int(sys.argv[2]);lib='/tmp/sparse-build' if mode=='legacy' else '/tmp/sparse-sharing-final-build'
st.generalized_evaluate_one(s.load(lib+'/_sparse_qualification.cpython-312-x86_64-linux-gnu.so'),'/tmp/poker-public-response-build','docs/qa/sparse-generalization-20261124',seed,mode,confirm=mode!='detailed')
