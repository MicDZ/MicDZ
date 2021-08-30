syntax on
let mapleader=" "

set nu
set norelativenumber
set cursorline
set wrap
set showcmd
set wildmenu
set hlsearch
set incsearch
set smartcase
set tabstop=4
set autoindent
set mouse=a

exec "nohlsearch"
color desert

noremap j h
noremap i k
noremap h i
noremap k j
noremap = nzz
noremap - Nzz
noremap <LEADER><CR> :nohlsearch<CR>

map af :set splitright<CR>:vsplit<CR>
map as :set nosplitright<CR>:vsplit<CR>
map ae :set nosplitbelow<CR>:split<CR>
map ad :set splitbelow<CR>:split<CR>

map <LEADER>f <C-w>l
map <LEADER>e <C-w>k
map <LEADER>s <C-w>h
map <LEADER>d <C-w>j

call plug#begin('~/.vim/plugged')
Plug 'vim-airline/vim-airline'
Plug 'connorholyday/vim-snazzy'
call plug#end()

colorscheme snazzy

map <F5> :call CompileRun()<CR>
map <F6> :!./%< <CR>
map <F7> <F5><F6>
func! CompileRun()
    exec "w"
    if &filetype == 'c'
        exec '!g++ -g % -o %<'
        exec '!time ./%<'
    elseif &filetype == 'cpp'
        exec '!g++ -g % -o %<'
        exec '!time ./%<'
    elseif &filetype == 'python'
        exec '!time python %'
    elseif &filetype == 'sh'
        :!time bash %
    endif
endfunc
