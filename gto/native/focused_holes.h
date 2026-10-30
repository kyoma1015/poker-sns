// Joint hole-deal proposal only. Native chance/policy/action semantics unchanged.
inline std::pair<double,double> focused_hole_probabilities(int n,const std::vector<int64_t>& world,const std::vector<int64_t>& target){
 if(n<4||n>52||world.size()!=4||target.size()!=2||target[0]==target[1])throw std::runtime_error("focused deal shape");
 auto sorted=world;std::sort(sorted.begin(),sorted.end());
 if(sorted.front()<0||sorted.back()>=n||std::adjacent_find(sorted.begin(),sorted.end())!=sorted.end()||target[0]<0||target[1]<0||target[0]>=n||target[1]>=n)throw std::runtime_error("focused deal cards");
 const double p=1./(double(n)*(n-1)*(n-2)*(n-3));
 const double specific=world[2]==target[0]&&world[3]==target[1]?1./(double(n-2)*(n-3)):0.;
 return {p,.1*p+.9*specific};
}
inline std::vector<int64_t> focused_hole_draw(std::mt19937& rng,int n,const std::vector<int64_t>& target){
 if(n<4||n>52||target.size()!=2||target[0]==target[1]||target[0]<0||target[1]<0||target[0]>=n||target[1]>=n)throw std::runtime_error("focused draw inputs");
 absl::uniform_real_distribution<double> coin(0,1);bool focus=coin(rng)<.9;
 std::vector<int64_t> deck;for(int c=0;c<n;++c)if(!focus||(c!=target[0]&&c!=target[1]))deck.push_back(c);
 std::vector<int64_t> world;for(int i=0;i<(focus?2:4);++i){
  std::vector<double> weights(deck.size(),1.);absl::discrete_distribution<int> draw(weights.begin(),weights.end());
  int index=draw(rng);world.push_back(deck[index]);deck.erase(deck.begin()+index);
 }
 if(focus){world.push_back(target[0]);world.push_back(target[1]);}return world;
}
