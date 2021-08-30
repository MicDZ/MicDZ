syntax on
set nu
set norelativenumber
set cursorline
set wrap
set showcmd
set wildmenu
set hlsearch
set incsearch
set smartcase

exec "nohlsearch"
color desert

noremap j h
noremap i k
noremap h i
noremap k j
noremap = nzz
noremap - Nzz

call plug#begin('~/.vim/plugged')

Plug 'vim-airline/vim-airline'
Plug 'connorholyday/vim-snazzy'
call plug#end()

colorscheme snazzy
