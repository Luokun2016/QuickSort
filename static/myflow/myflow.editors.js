(function($){
var myflow = $.myflow;

$.extend(true, myflow.editors, {
	inputEditor : function(){
		var _props,_k,_div,_src,_r;
		this.init = function(props, k, div, src, r){
			_props=props; _k=k; _div=div; _src=src; _r=r;
			$('<input  placeholder="请输入IP格式" style="width:100%;color:#000;" class="form-control topself_input"/>').val(props[_k].value).change(function(){
				var reg = new RegExp(/((2[0-4]\d|25[0-5]|[01]?\d\d?)\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?)/g);
				if(reg.test($(this).val())==false)
				{Showbo.Msg.alert("IP格式不正确将无法自动配IP");}

				props[_k].value = $(this).val();
				//$(_r).trigger('textchange', [$(this).val(), _src]);
			}).appendTo('#'+_div);
			
			$('#'+_div).data('editor', this);
		}
		this.destroy = function(){
			$('#'+_div+' input').each(function(){
				_props[_k].value = $(this).val();
			});
		}
	},
	textEditor : function(){
		var _props,_k,_div,_src,_r;
		this.init = function(props, k, div, src, r){
			_props=props; _k=k; _div=div; _src=src; _r=r;
			$('<input  placeholder="请输入设备名称" style="width:100%;color:#000;" class="form-control topself_input"/>').val(props[_k].value).change(function(){
				props[_k].value = $(this).val();
				$(_r).trigger('textchange', [$(this).val(), _src]);
			}).appendTo('#'+_div);

			$('#'+_div).data('editor', this);
		}
		this.destroy = function(){
			$('#'+_div+' input').each(function(){
				_props[_k].value = $(this).val();
			});
		}
	},
	labelEditor : function() {
		var _props, _k, _div, _src, _r;
		this.init = function(props, k, div, src, r) {
			_props = props;
			_k = k;
			_div = div;
			_src = src;
			_r = r;
			//alert(_k);

			$('<input type  style="width:100%;color:#000;" class="form-control topself_input" readonly/>').val(props[_k].value).change(
					function() {

						props[_k].value = $(this).val();
						$(_r).trigger('textchange', [$(this).val(), _src]);
					}).appendTo('#' + _div);
			$('#' + _div).data('editor', this);
		};
		this.destroy = function() {
			$('#' + _div + ' input').each(function() {
						_props[_k].value = $(this).val();
					});
		};
	},
	myselectEditor : function() {
		var _props, _k, _div, _src, _r;
		this.init = function(props, k, div, src, r) {
			_props = props;
			_k = k;
			_div = div;
			_src = src;
			_r = r;
			//alert(_k);

			$('<select  id="isconsole" style="width:100%;color:#000;" class="form-control"><option value="1">是</option><option value="0">否</option></select>').val(props[_k].value).change(
					function() {
						props[_k].value = $(this).val();
						//$(_r).trigger('textchange', [$(this).val(), _src]);
					}).appendTo('#' + _div);
			//$("#isconsole").val("0");

			// $('<option value="1">是</option>').appendTo('#isconsole');
			// $('<option value="0">否</option>').appendTo('#isconsole');

			$('#' + _div).data('editor', this);
		};
		this.destroy = function() {
			$('#' + _div + ' input').each(function() {
						_props[_k].value = $(this).val();
					});
		};
	},
	selectEditor : function(arg){
		var _props,_k,_div,_src,_r;
		this.init = function(props, k, div, src, r){
			_props=props; _k=k; _div=div; _src=src; _r=r;

			var sle = $('<select  style="width:100%;color:#000;" class="form-control"/>').val(props[_k].value).change(function(){
				props[_k].value = $(this).val();
			}).appendTo('#'+_div);
			
			if(typeof arg === 'string'){
				$.ajax({
				   type: "GET",
				   url: arg,
				   success: function(data){
					  var opts = eval(data);
					 if(opts && opts.length){
						for(var idx=0; idx<opts.length; idx++){
							sle.append('<option value="'+opts[idx].value+'">'+opts[idx].name+'</option>');
						}
						sle.val(_props[_k].value);
					 }
				   }
				});
			}else {
				for(var idx=0; idx<arg.length; idx++){
					sle.append('<option value="'+arg[idx].value+'">'+arg[idx].name+'</option>');
				}
				sle.val(_props[_k].value);
			}
			
			$('#'+_div).data('editor', this);
		};
		this.destroy = function(){
			$('#'+_div+' input').each(function(){
				_props[_k].value = $(this).val();
			});
		};
	}
});

})(jQuery);