// Behavioral cashflow coefficients by OWN private types/public history.
#include <vector>
#include <cmath>
extern "C" int root_coeff(int n,int h,int v,const int*actor,const int*count,const int*child,const double*c0,const double*c1,const double*p,double*out0,double*out1){
 if(n<1||h<1||v<1)return -1;std::vector<int>off(n+1);
 for(int k=0;k<n;++k){if(actor[k]<-1||actor[k]>1||count[k]<0||count[k]>4||(actor[k]<0?count[k]!=0:count[k]<2))return -2;off[k+1]=off[k]+(actor[k]<0?0:(actor[k]==0?h:v)*count[k]);for(int a=0;a<count[k];++a)if(child[k*4+a]<=k||child[k*4+a]>=n)return -3;}
 std::vector<double>a(n),b(n);
 for(int i=0;i<h;++i)for(int j=0;j<v;++j){for(int k=n-1;k>=0;--k){if(actor[k]<0){a[k]=c0[k];b[k]=c1[k];}else{a[k]=b[k]=0;int t=actor[k]==0?i:j;for(int x=0;x<count[k];++x){double q=p[off[k]+t*count[k]+x];a[k]+=q*a[child[k*4+x]];b[k]+=q*b[child[k*4+x]];}}}out0[i*v+j]=a[0];out1[i*v+j]=b[0];}return 0;
}
