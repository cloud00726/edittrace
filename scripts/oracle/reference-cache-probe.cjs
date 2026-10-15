// A reproducible observation of the pinned reference, not a claim about all releases.
const fs=require('fs'),path=require('path');
const {TextDocument}=process.argv[2]?require(path.resolve(process.argv[2])):require('vscode-languageserver-textdocument');
const initial='\ne\u0301\n';
const edit={range:{start:{line:1,character:2},end:{line:1,character:2}},text:'\r'};
const d=TextDocument.create('file:///probe','text',1,initial);
TextDocument.update(d,[edit],2);
const fresh=TextDocument.create(d.uri,'text',2,d.getText());
const result={reference:'vscode-languageserver-textdocument@1.0.12',initial,edit,result:d.getText(),cached_end_position:d.positionAt(d.getText().length),fresh_end_position:fresh.positionAt(fresh.getText().length),interpretation:'Pinned reference line-index observation; EditTrace oracle recreates the reference after each edit. Not a report about a third-party language server.'};
const target=path.resolve(__dirname,'../../tests/oracle/reference-cache-observation.json');
fs.writeFileSync(target,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
