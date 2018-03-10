/* 
(c) 2011 Lubomir Krupa, CC BY-ND 3.0
*/

$(document).ready(function(){

	var num = 1;//numberOfScreens;

	for(var i=1;i<=num;i++){
		$('#name'+i).html(blockName[i]);
	}
	var hoverEffect = true;
	// 鼠标经过效果
	if(hoverEffect){
		for(i=1;i<=num;i++){
			$('<style>#wrapper'+i+' div:hover{border: 1px #fff solid;box-shadow: 0px 0px 5px #fff;margin-left:4px;margin-top:4px;}</style>').appendTo('head');
		};
	};
	
	// 调整place位置
	var windowWidth = $(window).width();
	var windowHeight = $(window).height();
	var left1 = Math.floor((windowWidth - 1182)/2);
	var wrapperTop = Math.floor((windowHeight - 571)/2)-96;
	
	$('#place').css({'left':left1,'top':wrapperTop});
	$('#wrapper1 input:text').focus();
	
	// 点击链接
	var j=0;
	for (j=0; j <= (num-1); j++) {		
		for(i=0;i<=13;i++){								
			var title = bookmark[j][i]['title'];
			var url = bookmark[j][i]['url'];
			var thumb = bookmark[j][i]['thumb'];
			if(thumb==''){
				$('#thumb'+(j+1)+'-'+(i+1)).html('<a href="'+url+'" class="animsition-link" ><div class="title">'+title+'</div></a>');
			}
			else{
				$('#thumb'+(j+1)+'-'+(i+1)).html('<a href="'+url+'" class="animsition-link" ><img src="thumbs/'+thumb+'" /></a>');
			}
		};
	};

});
