syntax on
set showmode
" set noet ci pi sts=0 sw=4 ts=4 - same as the next 6 lines
set noexpandtab
set copyindent
set preserveindent
set softtabstop=0
set shiftwidth=4
set tabstop=4
set number
set autoindent
set smartindent
" Yank and Paste between terminal windows
set mouse=v
set clipboard=unnamed
autocmd FileType yaml setlocal ts=2 sts=2 sw=2 expandtab
autocmd FileType tex,latex,python set showmatch
"Python Settings
autocmd FileType python set softtabstop=4
autocmd FileType python set tabstop=4
autocmd FileType python set autoindent
autocmd FileType python set expandtab
autocmd FileType python set textwidth=132
autocmd FileType python set smartindent
autocmd FileType python set shiftwidth=4
autocmd FileType python map <buffer> <F2> :w<CR>:exec '! python' shellescape(@%, 1)<CR>
autocmd FileType python imap <buffer> <F2> <esc>:w<CR>:exec '! python' shellescape(@%, 1)<CR>
if has("autocmd")
  au BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") | exe "normal! g`\"" | endif
endif
"Undo file history
set undodir=~/.vim/undodir
set undofile
set undolevels=1000
set undoreload=10000

