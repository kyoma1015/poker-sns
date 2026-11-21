// Reuse original finite CFR/rank code without modifying it.
#include "core.cc"
extern "C" int range_kernel(int m,const int*board,int b,const double*r0,const double*r1,double*p,double*s,int*bucket,double*mass){
 if(m<3||m>5||b<2||b>32)return -1;
 std::vector<std::array<int,2>> hs;std::vector<uint64_t>rank;std::vector<uint64_t>unique;
 for(int a=0;a<52;++a)for(int c=a+1;c<52;++c){
  hs.push_back({a,c});bool bad=false;for(int k=0;k<m;++k)bad|=board[k]==a||board[k]==c;
  if(bad){rank.push_back(0);continue;}
  V cards{a,c};for(int k=0;k<m;++k)cards.push_back(board[k]);V result;
  if(cards.size()==5)result=five(cards);else if(cards.size()==7)result=rank7(cards);
  else for(int j=0;j<6;++j){V sub;for(int k=0;k<6;++k)if(k!=j)sub.push_back(cards[k]);result=std::max(result,five(sub));}
  uint64_t v=0;for(int k=0;k<6;++k)v=v*15+(k<int(result.size())?result[k]:0);
  rank.push_back(v);unique.push_back(v);
 }
 std::sort(unique.begin(),unique.end());unique.erase(std::unique(unique.begin(),unique.end()),unique.end());
 for(int i=0;i<1326;++i)bucket[i]=rank[i]?std::min(b-1,int((std::lower_bound(unique.begin(),unique.end(),rank[i])-unique.begin())*b/unique.size())):-1;
 std::fill(p,p+b*b,0.);std::fill(s,s+b*b,0.);*mass=0.;
 for(int i=0;i<1326;++i)if(bucket[i]>=0&&r0[i]>0)for(int j=0;j<1326;++j)if(bucket[j]>=0&&r1[j]>0){
  if(hs[i][0]==hs[j][0]||hs[i][0]==hs[j][1]||hs[i][1]==hs[j][0]||hs[i][1]==hs[j][1])continue;
  double w=r0[i]*r1[j];int k=bucket[i]*b+bucket[j];p[k]+=w;s[k]+=w*((rank[i]>rank[j])-(rank[i]<rank[j]));*mass+=w;
 }
 if(*mass<=0)return -2;
 for(int k=0;k<b*b;++k){s[k]=p[k]>0?s[k]/p[k]:0.;p[k]/=*mass;}return 0;
}
