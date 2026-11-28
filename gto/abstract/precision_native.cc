// Exact conditional showdown integration; separate from the frozen CFR engine.
#include <algorithm>
#include <array>
#include <cstdint>
#include <vector>
static int straight(unsigned bits){for(int h=14;h>=6;--h)if((bits&(31u<<(h-4)))==(31u<<(h-4)))return h;return (bits&0x403cu)==0x403cu?5:0;}
static uint64_t encode(std::array<int,6> v){uint64_t z=0;for(int x:v)z=z*15+x;return z;}
static uint64_t fast(const int*cards){
 int counts[15]{},suits[4]{};unsigned mask=0,sm[4]{};
 for(int k=0;k<7;++k){int r=cards[k]/4+2,s=cards[k]%4;++counts[r];++suits[s];mask|=1u<<r;sm[s]|=1u<<r;}
 int flush=-1;for(int s=0;s<4;++s)if(suits[s]>=5)flush=s;
 if(flush>=0){int st=straight(sm[flush]);if(st)return encode({8,st,0,0,0,0});}
 int quad=0,triple=0,pair=0;
 for(int r=14;r>=2;--r){if(counts[r]==4)quad=r;if(!triple&&counts[r]>=3)triple=r;}
 if(quad){int k=14;while(k==quad||!counts[k])--k;return encode({7,quad,k,0,0,0});}
 if(triple)for(int r=14;r>=2;--r)if(r!=triple&&counts[r]>=2){pair=r;break;}
 if(triple&&pair)return encode({6,triple,pair,0,0,0});
 if(flush>=0){std::array<int,6>out{5,0,0,0,0,0};int k=1;for(int r=14;r>=2&&k<6;--r)if(sm[flush]&(1u<<r))out[k++]=r;return encode(out);}
 int st=straight(mask);if(st)return encode({4,st,0,0,0,0});
 if(triple){std::array<int,6>out{3,triple,0,0,0,0};int k=2;for(int r=14;r>=2&&k<4;--r)if(r!=triple&&counts[r])out[k++]=r;return encode(out);}
 int p1=0,p2=0;for(int r=14;r>=2;--r)if(counts[r]>=2){if(!p1)p1=r;else if(!p2)p2=r;}
 if(p2){int k=14;while(k==p1||k==p2||!counts[k])--k;return encode({2,p1,p2,k,0,0});}
 if(p1){std::array<int,6>out{1,p1,0,0,0,0};int k=2;for(int r=14;r>=2&&k<5;--r)if(r!=p1&&counts[r])out[k++]=r;return encode(out);}
 std::array<int,6>out{};int k=1;for(int r=14;r>=2&&k<6;--r)if(counts[r])out[k++]=r;return encode(out);
}
extern "C" uint64_t precision_rank7(const int*cards){return fast(cards);}
extern "C" int precision_exact(const int*hole,const int*flop,int flop_count,uint64_t*out){
 if(flop_count!=0&&flop_count!=3)return -1;bool used[52]{};
 for(int k=0;k<4;++k){if(hole[k]<0||hole[k]>=52||used[hole[k]])return -2;used[hole[k]]=true;}
 for(int k=0;k<flop_count;++k){if(flop[k]<0||flop[k]>=52||used[flop[k]])return -2;used[flop[k]]=true;}
 std::vector<int> deck;for(int c=0;c<52;++c)if(!used[c])deck.push_back(c);
 int a[7]{hole[0],hole[1]},b[7]{hole[2],hole[3]};for(int k=0;k<flop_count;++k)a[k+2]=b[k+2]=flop[k];
 out[0]=out[1]=out[2]=0;
 auto settle=[&](){auto x=fast(a),y=fast(b);++out[x>y?0:x==y?1:2];};
 if(flop_count==3){for(int i=0;i<45;++i)for(int j=i+1;j<45;++j){a[5]=b[5]=deck[i];a[6]=b[6]=deck[j];settle();}}
 else for(int i=0;i<44;++i)for(int j=i+1;j<45;++j)for(int k=j+1;k<46;++k)for(int l=k+1;l<47;++l)for(int m=l+1;m<48;++m){a[2]=b[2]=deck[i];a[3]=b[3]=deck[j];a[4]=b[4]=deck[k];a[5]=b[5]=deck[l];a[6]=b[6]=deck[m];settle();}
 return 0;
}
#include <random>
static bool strong5(const std::array<int,2>&h,const std::array<int,3>&f){
 int suits[4]{};unsigned mask=0;bool pair=false;for(int c:{h[0],h[1],f[0],f[1],f[2]}){unsigned bit=1u<<(c/4+2);if(mask&bit)pair=true;mask|=bit;++suits[c%4];}
 return pair||straight(mask)||*std::max_element(suits,suits+4)>=4;
}
static void conditional(const std::array<int,4>&h,const std::array<int,3>&f,uint64_t*out){precision_exact(h.data(),f.data(),3,out);}
extern "C" int precision_kernel(int n,const int*offset,const int*cards,int samples,int seed,const uint8_t*exact,const double*exactvalue,double*mean,double*variance){
 if(n!=169||samples<2)return -1;std::mt19937 rng(seed);int xs[4]{2,5,18,42};
 for(int i=0;i<n;++i)for(int j=i;j<n;++j){
  std::vector<std::array<int,4>>deals;for(int a=offset[i];a<offset[i+1];++a)for(int b=offset[j];b<offset[j+1];++b){int x=cards[2*a],y=cards[2*a+1],z=cards[2*b],w=cards[2*b+1];if(x!=z&&x!=w&&y!=z&&y!=w)deals.push_back({x,y,z,w});}
  double sum[2][5]{},sq[2][5]{};
  for(int s=0;s<samples;++s){auto h=deals[std::uniform_int_distribution<size_t>(0,deals.size()-1)(rng)];std::vector<int>deck;for(int c=0;c<52;++c)if(std::find(h.begin(),h.end(),c)==h.end())deck.push_back(c);
   // Consume all five original draws to preserve the previous random flop stream.
   for(int k=0;k<5;++k){int q=std::uniform_int_distribution<int>(k,47)(rng);std::swap(deck[k],deck[q]);}
   std::array<int,3>f{deck[0],deck[1],deck[2]};std::array<int,2>a{h[0],h[1]},b{h[2],h[3]};bool sa=strong5(a,f),sb=strong5(b,f);
   int top=std::max({f[0]/4,f[1]/4,f[2]/4});bool pa=sa||(a[0]/4>top&&a[1]/4>top),pb=sb||(b[0]/4>top&&b[1]/4>top);
   bool fold[2]{(sb&&!sa)||(!sb&&pa&&!sb),(sa&&!sb)||(!sa&&pb&&!sa)};
   // BB's call predicate is the same strength predicate as its lead; retained
   // exactly as the original fixed controller, not silently improved here.
   int winner[2]{sb?-1:1,sa?-1:1};bool bet[2]{sb||pa,sa||pb};
   bool needed=false;for(int k=0;k<5;++k)if(!exact[k*n*n+i*n+j]&&(k==0||!fold[0]||!fold[1]))needed=true;
   double equity=0;if(needed){uint64_t counts[3];conditional(h,f,counts);equity=(double(counts[0])-double(counts[2]))/990.;}
   for(int d=0;d<2;++d)for(int k=0;k<5;++k){int pos=k*n*n+(d?j*n+i:i*n+j);double value;
    if(exact[pos])value=exactvalue[pos];else if(k==0)value=(d?-1:1)*100*equity;
    else {int x=xs[k-1];value=fold[d]?winner[d]*x:(d?-1:1)*equity*(x+(bet[d]?std::min(x,100-x):0));}
    // Shared swapped-seat worlds for diagonal classes.
    if(i==j){double other;if(exact[pos])other=value;else if(k==0)other=-value;else{int x=xs[k-1];other=fold[1-d]?winner[1-d]*x:(d?1:-1)*equity*(x+(bet[1-d]?std::min(x,100-x):0));}value=(value+other)/2;}
    sum[d][k]+=value;sq[d][k]+=value*value;
   }
  }
  for(int d=0;d<2;++d)for(int k=0;k<5;++k){int pos=k*n*n+(d?j*n+i:i*n+j);mean[pos]=exact[pos]?exactvalue[pos]:sum[d][k]/samples;variance[pos]=exact[pos]?0.:std::max(0.,(sq[d][k]-sum[d][k]*sum[d][k]/samples)/(samples-1));}
 }return 0;
}
