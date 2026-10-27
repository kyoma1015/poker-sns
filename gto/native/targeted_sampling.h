// Experimental proposal only: game, target policy and importance equations stay intact.
inline std::vector<double> ordinary_proposal(const std::vector<double>& current,double epsilon,
    const std::vector<int64_t>& actions,int round,int raises){
 if(current.empty()||current.size()!=actions.size()||!std::isfinite(epsilon)||epsilon<=0||epsilon>1||round<0||round>3||raises<0)throw std::runtime_error("proposal inputs");
 double total=0;for(double p:current){if(!std::isfinite(p)||p<0)throw std::runtime_error("proposal policy");total+=p;}if(std::abs(total-1)>1e-12)throw std::runtime_error("proposal normalization");
 auto sorted=actions;std::sort(sorted.begin(),sorted.end());if(sorted.front()<0||std::adjacent_find(sorted.begin(),sorted.end())!=sorted.end())throw std::runtime_error("proposal actions");
 const int64_t target=raises==0?7:raises==1?20:raises==2?44:1;
 const bool focused=round==0&&std::find(actions.begin(),actions.end(),target)!=actions.end();
 std::vector<double> sampling;sampling.reserve(current.size());
 for(size_t i=0;i<current.size();++i){
  double q=focused?.1/current.size()+.9*(actions[i]==target):1./current.size();
  sampling.push_back((1-epsilon)*current[i]+epsilon*q);
 }
 return sampling;
}
