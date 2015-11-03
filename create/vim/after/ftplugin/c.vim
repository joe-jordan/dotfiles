" tabs are actually two spaces
set ts=8 sts=2 sw=2 expandtab

" remove whitespace from the end of lines.
autocmd BufWritePre * :%s/\s\+$//e 

"highlight EOL whitespace
autocmd InsertEnter * syn clear EOLWS | syn match EOLWS excludenl /\s\+\%#\@!$/
autocmd InsertLeave * syn clear EOLWS | syn match EOLWS excludenl /\s\+$/
highlight EOLWS ctermbg=red guibg=red


