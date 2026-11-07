// All class-pair counterfactual payoffs; no reached-range weights in this oracle.
#include <vector>
#include <cstdint>
extern "C" int fullsupport(int n,int planes,const int*cards,const int*labels,const int*groups,const uint16_t*w,const uint16_t*t,const double*a,const double*b,const int*full,double*out,double*mass){
 if(n<1||n>1176||planes<1||planes>64)return -1;const int S=169*169;std::vector<uint64_t>mask(n);std::vector<int>counts(S);std::vector<long double>sum((size_t)planes*S);
 for(int i=0;i<n;++i){if(labels[i]<0||labels[i]>=169||groups[i]<0||groups[i]>=8)return -2;mask[i]=(1ull<<cards[2*i])|(1ull<<cards[2*i+1]);}
 for(int i=0;i<n;++i)for(int j=0;j<n;++j)if(!(mask[i]&mask[j])){int k=labels[i]*169+labels[j],g=groups[i]*8+groups[j];long double e=((long double)w[i*n+j]+(long double)t[i*n+j]/2)/990;++counts[k];for(int p=0;p<planes;++p)sum[(size_t)p*S+k]+=a[p*64+g]+b[p*64+g]*e;}
 for(int k=0;k<S;++k){if(full[k]<=0)return -3;long double scale=1.L/((long double)full[k]*17296);mass[k]=counts[k]*scale;for(int p=0;p<planes;++p)out[(size_t)p*S+k]=sum[(size_t)p*S+k]*scale;}return 0;
}
extern "C" int oracle_update(int planes,int sample,const double*y,const double*mass,const double*c,double*mean,double*m2){
 if(planes<1||sample<1)return -1;const int S=169*169;
 for(int p=0;p<planes;++p)for(int j=0;j<S;++j){int k=p*S+j;double x=c[k]+22100*(y[k]-c[k]*mass[j]),d=x-mean[k];mean[k]+=d/sample;m2[k]+=d*(x-mean[k]);}return 0;
}
extern "C" int scalar_update(int planes,int rows,int sample,const double*y,const double*mass,const double*c,const double*weights,const double*constant,double*mean,double*m2){
 if(planes<1||rows<1||sample<1)return -1;int N=planes*169*169;std::vector<double>values(constant,constant+rows);
 for(int k=0;k<N;++k){double x=c[k]+22100*(y[k]-c[k]*mass[k%(169*169)]);for(int r=0;r<rows;++r)values[r]+=weights[(size_t)r*N+k]*x;}
 for(int r=0;r<rows;++r){double d=values[r]-mean[r];mean[r]+=d/sample;m2[r]+=d*(values[r]-mean[r]);}return 0;
}
