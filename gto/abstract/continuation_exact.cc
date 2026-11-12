// Full board/flop-partition expectations; no Monte Carlo or reference fitting.
#include "precision_native.cc"
static bool lead2(const std::array<int,2>&h,const std::array<int,3>&f){
 int ranks[13]{},suits[4]{},pairs=0;unsigned mask=0;
 for(int c:{h[0],h[1],f[0],f[1],f[2]}){++ranks[c/4];++suits[c%4];mask|=1u<<(c/4+2);}
 for(int n:ranks){if(n>=3)return true;if(n>=2)++pairs;}
 return pairs>=2||straight(mask)||*std::max_element(suits,suits+4)>=5;
}
struct Form{int8_t constant[4]{},coefficient[4]{};};
static Form forms(const int*h,const std::array<int,3>&f){
 std::array<int,2>a{h[0],h[1]},b{h[2],h[3]};bool strength[2]{strong5(a,f),strong5(b,f)},lead[2]{lead2(a,f),lead2(b,f)};
 int top=std::max({f[0]/4,f[1]/4,f[2]/4});bool probe[2]{strength[0]||(a[0]/4>top&&a[1]/4>top),strength[1]||(b[0]/4>top&&b[1]/4>top)};Form result;
 for(int variant=0;variant<2;++variant)for(int d=0;d<2;++d){int sb=d,bb=1-d,k=variant*2+d;bool bet=variant?lead[bb]:strength[bb];
  if(bet&&!strength[sb])result.constant[k]=-1;
  else if(!bet&&probe[sb]&&!strength[bb])result.constant[k]=1;
  else result.coefficient[k]=(bet||probe[sb]?2:1)*(d?-1:1);
 }return result;
}
extern "C" int precision_controller_board(const int*h,const int*board,int64_t*out){
 for(int k=0;k<4;++k)out[k]=0;int a[7]{h[0],h[1]},b[7]{h[2],h[3]};for(int k=0;k<5;++k)a[k+2]=b[k+2]=board[k];auto x=fast(a),y=fast(b);int sign=(x>y)-(x<y);
 for(int i=0;i<3;++i)for(int j=i+1;j<4;++j)for(int k=j+1;k<5;++k){auto f=forms(h,{board[i],board[j],board[k]});for(int v=0;v<4;++v)out[v]+=f.constant[v]+sign*f.coefficient[v];}return 0;
}
extern "C" int precision_controller_exact(const int*h,int64_t*out){
 bool used[52]{};for(int i=0;i<4;++i){if(h[i]<0||h[i]>=52||used[h[i]])return -1;used[h[i]]=true;}
 std::vector<int>d;for(int c=0;c<52;++c)if(!used[c])d.push_back(c);std::vector<Form>cache(48*48*48);
 for(int i=0;i<46;++i)for(int j=i+1;j<47;++j)for(int k=j+1;k<48;++k)cache[(i*48+j)*48+k]=forms(h,{d[i],d[j],d[k]});
 for(int v=0;v<5;++v)out[v]=0;int a[7]{h[0],h[1]},b[7]{h[2],h[3]};
 for(int i=0;i<44;++i)for(int j=i+1;j<45;++j)for(int k=j+1;k<46;++k)for(int l=k+1;l<47;++l)for(int m=l+1;m<48;++m){
  int indices[5]{i,j,k,l,m};for(int v=0;v<5;++v)a[v+2]=b[v+2]=d[indices[v]];auto x=fast(a),y=fast(b);int sign=(x>y)-(x<y);out[0]+=sign;
  for(int p=0;p<3;++p)for(int q=p+1;q<4;++q)for(int r=q+1;r<5;++r){const auto&f=cache[(indices[p]*48+indices[q])*48+indices[r]];for(int v=0;v<4;++v)out[v+1]+=f.constant[v]+sign*f.coefficient[v];}
 }return 0;
}
