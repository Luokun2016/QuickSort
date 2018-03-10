(function($){
var myflow = $.myflow;

$.extend(true,myflow.config.rect,{
	attr : {
	r : 8,
	fill : '#F6F7FF',
	stroke : '#03689A',
	"stroke-width" : 2
},margin:0
});

$.extend(true,myflow.config.tools.states,{
			start : {showType: 'image&text',
				type : 'start',
				name : {text:'<<start>>'},
				text : {text:'开始'},
				img : {src : '/statics/myflow/img/48/start_event_empty.png',width : 48, height:48},
				attr : {width:50 ,heigth:50 },
				props : {
					text: {name:'text',label: '显示', value:'', editor: function(){return new myflow.editors.textEditor();}, value:'开始'},
					temp1: {name:'temp1', label : '文本', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					temp2: {name:'temp2', label : '选择', value:'', editor: function(){return new myflow.editors.selectEditor([{name:'aaa',value:1},{name:'bbb',value:2}]);}}
				}},
			end : {showType: 'image',type : 'end',
				name : {text:'<<end>>'},
				text : {text:'结束'},
				img : {src : '/statics/myflow/img/48/end_event_terminate.png',width : 48, height:48},
				attr : {width:50 ,heigth:50 },
				props : {
					text: {name:'text',label: '显示', value:'', editor: function(){return new myflow.editors.textEditor();}, value:'结束'},
					temp1: {name:'temp1', label : '文本', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					temp2: {name:'temp2', label : '选择', value:'', editor: function(){return new myflow.editors.selectEditor([{name:'aaa',value:1},{name:'bbb',value:2}]);}}
				}},
			'end-cancel' : {showType: 'image',type : 'end-cancel',
				name : {text:'<<end-cancel>>'},
				text : {text:'取消'},
				img : {src : '/statics/myflow/img/48/end_event_cancel.png',width : 48, height:48},
				attr : {width:50 ,heigth:50 },
				props : {
					text: {name:'text',label: '显示', value:'', editor: function(){return new myflow.editors.textEditor();}, value:'取消'},
					temp1: {name:'temp1', label : '文本', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					temp2: {name:'temp2', label : '选择', value:'', editor: function(){return new myflow.editors.selectEditor([{name:'aaa',value:1},{name:'bbb',value:2}]);}}
				}},
			'end-error' : {showType: 'image',type : 'end-error',
				name : {text:'<<end-error>>'},
				text : {text:'错误'},
				img : {src : '/statics/myflow/img/48/end_event_error.png',width : 48, height:48},
				attr : {width:50 ,heigth:50 },
				props : {
					text: {name:'text',label: '显示', value:'', editor: function(){return new myflow.editors.textEditor();}, value:'错误'},
					temp1: {name:'temp1', label : '文本', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					temp2: {name:'temp2', label : '选择', value:'', editor: function(){return new myflow.editors.selectEditor([{name:'aaa',value:1},{name:'bbb',value:2}]);}}
				}},
			state : {showType: 'text',type : 'state',
				name : {text:'<<state>>'},
				text : {text:'状态'},
				img : {src : '/statics/myflow/img/48/task_empty.png',width : 48, height:48},
				props : {
					text: {name:'text',label: '显示', value:'', editor: function(){return new myflow.editors.textEditor();}, value:'状态'},
					temp1: {name:'temp1', label : '文本', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					temp2: {name:'temp2', label : '选择', value:'', editor: function(){return new myflow.editors.selectEditor([{name:'aaa',value:1},{name:'bbb',value:2}]);}}
				}},
			fork : {showType: 'image',type : 'fork',
				name : {text:'<<fork>>'},
				text : {text:'分支'},
				img : {src : '/statics/myflow/img/48/gateway_parallel.png',width :48, height:48},
				attr : {width:50 ,heigth:50 },
				props : {
					text: {name:'text', label: '显示', value:'', editor: function(){return new myflow.editors.textEditor();}, value:'分支'},
					temp1: {name:'temp1', label: '文本', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					temp2: {name:'temp2', label : '选择', value:'', editor: function(){return new myflow.editors.selectEditor('select.json');}}
				}},
			join : {showType: 'image',type : 'join',
				name : {text:'<<join>>'},
				text : {text:'合并'},
				img : {src : '/statics/myflow/img/48/gateway_parallel.png',width :48, height:48},
				attr : {width:50 ,heigth:50 },
				props : {
					text: {name:'text', label: '显示', value:'', editor: function(){return new myflow.editors.textEditor();}, value:'合并'},
					temp1: {name:'temp1', label: '文本', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					temp2: {name:'temp2', label : '选择', value:'', editor: function(){return new myflow.editors.selectEditor('select.json');}}
				}},
			task : {showType: 'text',type : 'task',
				name : {text:'<<task>>'},
				text : {text:'---任务'},
				img : {src : '/statics/myflow/img/48/task_empty.png',width :48, height:48},
				props : {
					text: {name:'text', label: '显示', value:'', editor: function(){return new myflow.editors.textEditor();}, value:'任务'},
					assignee: {name:'assignee', label: '用户', value:'', editor: function(){return new myflow.editors.selectEditor('../js/myflow/select.json');}},
					desc: {name:'desc', label : '描述', value:'', editor: function(){return new myflow.editors.inputEditor();}},
            					type: {name:'type', label : '新增属性', value:'', editor: function(){return new myflow.editors.inputEditor();}},
				}},
			pc : {showType: 'image&text',type : 'pc',
				name : {text:'<<task>>'},
				text : {text:'终端设备'},
				img : {src : '/statics/myflow/img/128/pc.png',width :40, height:48},
				props : {
					text: {name:'text', label: '名称', value:'', editor: function(){return new myflow.editors.textEditor();}},
					addr: {name:'addr', label : '地址', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					desc: {name:'desc', label : '备注', value:'', editor: function(){return new myflow.editors.labelEditor();}},
					instance: {name:'instance', label : '实例', value:'', editor: function(){return new myflow.editors.labelEditor();}},
            					type: {name:'type', label : '类型', value:'', editor: function(){return new myflow.editors.labelEditor();}},
				}},
			pgate : {showType: 'image&text',type : 'pgate',
				name : {text:'<<task>>'},
				text : {text:'安全设备'},
				img : {src : '/statics/myflow/img/128/fw.png',width :40, height:48},
				props : {
					text: {name:'text', label: '名称', value:'', editor: function(){return new myflow.editors.textEditor();}},
					addr: {name:'addr', label : '地址', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					desc: {name:'desc', label : '备注', value:'', editor: function(){return new myflow.editors.labelEditor();}},
					instance: {name:'instance', label : '实例', value:'', editor: function(){return new myflow.editors.labelEditor();}},
            					type: {name:'type', label : '类型', value:'', editor: function(){return new myflow.editors.labelEditor();}},
				}},
			pswitch : {showType: 'image&text',type : 'pswitch',
				name : {text:'<<task>>'},
				text : {text:'网络设备'},
				img : {src : '/statics/myflow/img/128/switch.png',width :40, height:48},
				props : {
					text: {name:'text', label: '名称', value:'', editor: function(){return new myflow.editors.textEditor();}},
					addr: {name:'addr', label : '地址', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					desc: {name:'desc', label : '备注', value:'', editor: function(){return new myflow.editors.labelEditor();}},
					instance: {name:'instance', label : '实例', value:'', editor: function(){return new myflow.editors.labelEditor();}},
            					type: {name:'type', label : '类型', value:'', editor: function(){return new myflow.editors.labelEditor();}},
				}},
			imgls : {showType: 'image&text',type : 'imgls',
				name : {text:'<<task>>'},
				text : {text:'虚拟服务器'},
				img : {src : '/statics/myflow/img/128/*.png',width :40, height:48},
				props : {
					text: {name:'text', label: '名称', value:'', editor: function(){return new myflow.editors.textEditor();}},
					addr: {name:'addr', label : '地址', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					desc: {name:'desc', label : '备注', value:'', editor: function(){return new myflow.editors.labelEditor();}},
					instance: {name:'instance', label : '实例', value:'', editor: function(){return new myflow.editors.labelEditor();}},
            					type: {name:'type', label : '类型', value:'', editor: function(){return new myflow.editors.labelEditor();}},
            					isconsole: {name:'isconsole', label : '控制台', value:'', editor: function(){return new myflow.editors.myselectEditor();}},

				}},
			imgvgtls : {showType: 'image&text',type : 'imgvgtls',
				name : {text:'<<task>>'},
				text : {text:'虚拟网关'},
				img : {src : '/statics/myflow/img/128/*.png',width :40, height:48},
				props : {
					text: {name:'text', label: '名称', value:'', editor: function(){return new myflow.editors.textEditor();}},
					addr: {name:'addr', label : '地址', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					desc: {name:'desc', label : '备注', value:'', editor: function(){return new myflow.editors.labelEditor();}},
					instance: {name:'instance', label : '实例', value:'', editor: function(){return new myflow.editors.labelEditor();}},
            					type: {name:'type', label : '类型', value:'', editor: function(){return new myflow.editors.labelEditor();}},
				}},
			imgvshls : {showType: 'image&text',type : 'imgvshls',
				name : {text:'<<task>>'},
				text : {text:'虚拟交换'},
				img : {src : '/statics/myflow/img/128/*.png',width :40, height:48},
				props : {
					text: {name:'text', label: '名称', value:'', editor: function(){return new myflow.editors.textEditor();}},
					addr: {name:'addr', label : '地址', value:'', editor: function(){return new myflow.editors.inputEditor();}},
					desc: {name:'desc', label : '备注', value:'', editor: function(){return new myflow.editors.labelEditor();}},
					instance: {name:'instance', label : '实例', value:'', editor: function(){return new myflow.editors.labelEditor();}},
            					type: {name:'type', label : '类型', value:'', editor: function(){return new myflow.editors.labelEditor();}},
				}},
			decision : {showType: 'image',type : 'decision',
			name : {text:'<<decision>>'},
			text : {text:'决定'},
			img : {src : '/statics/myflow/img/48/gateway_parallel.png',width :48, height:48},
			attr : {width:50 ,heigth:50 },
			props : {
			    text: {name:'text', label: '显示', value:'', editor: function(){return new myflow.editors.textEditor();}, value:'决定'},
			    expr: {name:'expr', label : '表达式', value:'', editor: function(){return new myflow.editors.inputEditor();}},
			    desc: {name:'desc', label : '描述', value:'', editor: function(){return new myflow.editors.inputEditor();}}
			}}
});
})(jQuery);