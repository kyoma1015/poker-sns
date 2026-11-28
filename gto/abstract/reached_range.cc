// Conditional own-hand features from ALL hypothetical opponents,never dealt j.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <vector>
static_assert(std::numeric_limits<long double>::digits>=64,"extended sums required");
extern "C" int reached_features(int n,const int*holes,const int*labels,const uint16_t*w,const uint16_t*t,const double*reach,double*out){
 if(n<1||n>1176)return -1;std::vector<uint64_t>mask(n);
 for(int h=0;h<169;++h)if(!std::isfinite(reach[h])||reach[h]<0||reach[h]>1)return -2;
 for(int i=0;i<n;++i){int a=holes[i*2],b=holes[i*2+1];if(a<0||a>=52||b<0||b>=52||a==b||labels[i]<0||labels[i]>=169)return -3;mask[i]=(1ull<<a)|(1ull<<b);}
 for(int i=0;i<n;++i){long double z=0,e=0,wi=0,ti=0,hi=0,sq=0;
  for(int j=0;j<n;++j)if(!(mask[i]&mask[j])){long double q=reach[labels[j]],v=((long double)w[i*n+j]+(long double)t[i*n+j]/2)/990;z+=q;e+=q*v;wi+=q*w[i*n+j]/990;ti+=q*t[i*n+j]/990;hi+=q*(2*w[i*n+j]+t[i*n+j]>990);sq+=q*v*v;}
  out[i*6]=z;for(int k=1;k<6;++k)out[i*6+k]=0;
  if(z>0){out[i*6+1]=e/z;out[i*6+2]=wi/z;out[i*6+3]=ti/z;out[i*6+4]=hi/z;out[i*6+5]=std::sqrt(std::max((long double)0,sq/z-(e/z)*(e/z)));}
 }return 0;
}
