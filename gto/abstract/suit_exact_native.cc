#include <cstddef>
extern "C" int accumulate(int planes,int multiplicity,const double*y,const double*mass,long double*sum,long double*chance){
 if(planes<1||planes>64||multiplicity<1||multiplicity>24)return -1;int S=169*169;
 for(int i=0;i<S;++i)chance[i]+=(long double)multiplicity*mass[i];
 for(int i=0;i<planes*S;++i)sum[i]+=(long double)multiplicity*y[i];return 0;
}
