set tw=8 sts=4 sw=4 expandtab

"highlight EOL whitespace
autocmd InsertEnter * syn clear EOLWS | syn match EOLWS excludenl /\s\+\%#\@!$/
autocmd InsertLeave * syn clear EOLWS | syn match EOLWS excludenl /\s\+$/
highlight EOLWS ctermbg=red guibg=red


"highlight >80 columns
"let &colorcolumn=join(range(101,999),",") 
