function setflickr(total_page,current_page,dic){
    var innerhtml='';
    var m_innerhtml='';
    var innertext='';
    for (var key in dic) 
    {
      var mtext="&"+key+'='+dic[key];
      innertext+=mtext;
    }  

   for(var i = 1;i <= total_page;++i){
    // “上一页”不可用时与第一页
      if(total_page==1){
        innerhtml+='<span>上一页</span><span class="current">1</span><span>下一页</span>';
        continue;
      }    
      else if(i==1&&current_page==1){
        innerhtml+='<span>上一页</span><span class="current">1</span>';
        continue;
      }
  
      // “上一页”可用与第一页
      if(i==1&&current_page!=1){
         innerhtml+='<a href="?page='+(current_page-1)+innertext+'">上一页</a><a href="?page=1'+innertext+'">1</a>';
         continue;
      }

      if(current_page<6){
        if(i<6){
          if(current_page==i&&i!=total_page){
            innerhtml+='<span class="current">'+current_page+'</span>';
            continue;
          }
          if(current_page!=i&&i<total_page){
            innerhtml+='<a href="?page='+i+innertext+'" title="第'+i+'页">'+i+'</a>';
            continue;
          }
          if(total_page<6&&current_page!=total_page){
              innerhtml+='<a href="?page='+i+innertext+'" title="第'+i+'页">'+i+'</a><a href="?page='+(current_page+1)+innertext+'">下一页</a>';
              continue;
          }
          if(total_page<6&&current_page==total_page){
              innerhtml+='<span class="current">'+total_page+'</span><span>下一页</span>';
              continue;
          }        
        }
        else{
          if(i<total_page){
            continue;
          }
          else{
            if(total_page>=6){
             innerhtml+='<span class="current">...</span>';
            }
            innerhtml+='<a href="?page='+i+innertext+'" title="第'+i+'页">'+i+'</a><a href="?page='+(current_page+1)+innertext+'">下一页</a>';
            continue;
          }
        }
      }

      else{
        if(total_page-current_page<=4&&i>=total_page-4){ 
          if(i==total_page-4){
             innerhtml+='<span class="current">...</span>';
             if(current_page==i){
              innerhtml+='<span class="current">'+current_page+'</span>';
             }
            continue;
          }
          if(current_page==i&&i!=total_page){
            innerhtml+='<span class="current">'+current_page+'</span>';
            continue;
          }
          if(current_page!=i&&i<total_page){
            innerhtml+='<a href="?page='+i+innertext+'" title="第'+i+'页">'+i+'</a>';
            continue;
          }
          if(current_page!=i&&i==total_page){
            innerhtml+='<a href="?page='+total_page+innertext+'" title="第'+total_page+'页">'+total_page+'</a><a href="?page='+(current_page+1)+innertext+'">下一页</a>';
            continue;
          }     
          if(i==total_page){
            innerhtml+='<span class="current">'+i+'</span><span>下一页</span>';
          }     
        }

        else if(total_page-current_page>=4&&i==current_page){
          innerhtml+='<span class="current">...</span><a href="?page='+(i-1)+innertext+'" title="第'+(i-1)+'页">'+(i-1)+'</a><span class="current">'+i+'</span><a href="?page='+(i+1)+innertext+'" title="第'+(i+1)+'页">'+(i+1)+'</a><span class="current">...</span><a href="?page='+total_page+innertext+'" title="第'+total_page+'页">'+total_page+'</a><a href="?page='+(current_page+1)+innertext+'">下一页</a>';
        }
      }        
   }
   return innerhtml;
}