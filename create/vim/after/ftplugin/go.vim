" tabs are actually tabs, displayed as 4 spaces wide.
set ts=4 sw=4 sts=4

" remove whitespace from the end of lines.
autocmd BufWritePre * :%s/\s\+$//e 

"highlight EOL whitespace
autocmd InsertEnter * syn clear EOLWS | syn match EOLWS excludenl /\s\+\%#\@!$/
autocmd InsertLeave * syn clear EOLWS | syn match EOLWS excludenl /\s\+$/
highlight EOLWS ctermbg=red guibg=red

